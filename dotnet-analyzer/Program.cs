using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;

namespace LegacyLens.Analyzer
{
    public class RoslynEvidenceItem
    {
        public string Id { get; set; } = string.Empty;
        public string RelativePath { get; set; } = string.Empty;
        public string SymbolName { get; set; } = string.Empty;
        public int StartLine { get; set; }
        public int EndLine { get; set; }
        public string SourceExcerpt { get; set; } = string.Empty;
        public string Category { get; set; } = string.Empty;
        public string ExtractionMethod { get; set; } = "roslyn_compiler_ast";
        public Dictionary<string, string> Metadata { get; set; } = new();
    }

    public class BusinessRuleSyntaxWalker : CSharpSyntaxWalker
    {
        private readonly string _filePath;
        private readonly string _repoRoot;
        public List<RoslynEvidenceItem> Evidence { get; } = new();

        public BusinessRuleSyntaxWalker(string filePath, string repoRoot)
        {
            _filePath = filePath;
            _repoRoot = repoRoot;
        }

        public override void VisitIfStatement(IfStatementSyntax node)
        {
            var lineSpan = node.GetLocation().GetLineSpan();
            int startLine = lineSpan.StartLinePosition.Line + 1;
            int endLine = lineSpan.EndLinePosition.Line + 1;

            Evidence.Add(new RoslynEvidenceItem
            {
                Id = $"roslyn_{Guid.NewGuid():N}"[..15],
                RelativePath = Path.GetRelativePath(_repoRoot, _filePath).Replace("\\", "/"),
                SymbolName = node.Parent is MethodDeclarationSyntax m ? m.Identifier.Text : "ConditionBlock",
                StartLine = startLine,
                EndLine = endLine,
                SourceExcerpt = node.Condition.ToString(),
                Category = "business_rule",
                Metadata = new Dictionary<string, string>
                {
                    { "condition_kind", node.Condition.Kind().ToString() },
                    { "full_statement", node.ToString().Split('\n').FirstOrDefault()?.Trim() ?? string.Empty }
                }
            });

            base.VisitIfStatement(node);
        }

        public override void VisitMethodDeclaration(MethodDeclarationSyntax node)
        {
            var lineSpan = node.GetLocation().GetLineSpan();
            int startLine = lineSpan.StartLinePosition.Line + 1;
            int endLine = lineSpan.EndLinePosition.Line + 1;

            var attributes = node.AttributeLists
                .SelectMany(al => al.Attributes)
                .Select(a => a.Name.ToString())
                .ToList();

            if (attributes.Any(a => a.Contains("Http") || a.Contains("Authorize") || a.Contains("Route")))
            {
                Evidence.Add(new RoslynEvidenceItem
                {
                    Id = $"roslyn_{Guid.NewGuid():N}"[..15],
                    RelativePath = Path.GetRelativePath(_repoRoot, _filePath).Replace("\\", "/"),
                    SymbolName = node.Identifier.Text,
                    StartLine = startLine,
                    EndLine = endLine,
                    SourceExcerpt = node.DeclarationKeyword() + " " + node.Identifier.Text,
                    Category = "route",
                    Metadata = new Dictionary<string, string>
                    {
                        { "attributes", string.Join(",", attributes) },
                        { "return_type", node.ReturnType.ToString() }
                    }
                });
            }

            base.VisitMethodDeclaration(node);
        }

        private static string DeclarationKeyword() => "method";
    }

    public static class Program
    {
        public static int Main(string[] args)
        {
            if (args.Length < 1)
            {
                Console.WriteLine("Usage: LegacyLens.Analyzer <path-to-repo> [output-json-file]");
                return 1;
            }

            string repoRoot = Path.GetFullPath(args[0]);
            string outputFile = args.Length > 1 ? args[1] : "roslyn_evidence.json";

            if (!Directory.Exists(repoRoot))
            {
                Console.Error.WriteLine($"Repository directory not found: {repoRoot}");
                return 1;
            }

            var allEvidence = new List<RoslynEvidenceItem>();
            var csFiles = Directory.GetFiles(repoRoot, "*.cs", SearchOption.AllDirectories);

            foreach (var file in csFiles)
            {
                if (file.Contains("bin") || file.Contains("obj")) continue;

                string code = File.ReadAllText(file);
                SyntaxTree tree = CSharpSyntaxTree.ParseText(code);
                CompilationUnitSyntax root = tree.GetCompilationUnitRoot();

                var walker = new BusinessRuleSyntaxWalker(file, repoRoot);
                walker.Visit(root);
                allEvidence.AddRange(walker.Evidence);
            }

            var options = new JsonSerializerOptions { WriteIndented = true };
            string json = JsonSerializer.Serialize(allEvidence, options);
            File.WriteAllText(outputFile, json);

            Console.WriteLine($"Roslyn compiler analysis complete. Discovered {allEvidence.Count} evidence items. Saved to: {outputFile}");
            return 0;
        }
    }
}
