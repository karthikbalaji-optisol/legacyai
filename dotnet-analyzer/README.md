# LegacyLens Roslyn Code Analyzer

This companion service provides deep, compiler-level semantic analysis of C# codebases using the official **Microsoft.CodeAnalysis.CSharp (Roslyn)** compiler platform.

## When to Use

1. **Deterministic Python Scanner (Default)**:
   - Does not require .NET SDK installed on the host.
   - Fast, regex/AST-based scanner parsing controllers, methods, thresholds, and attributes.
   - Built directly into the LegacyLens backend and MCP server.

2. **Roslyn Semantic Analyzer (Optional Companion)**:
   - Requires .NET 8.0 SDK.
   - Performs full syntactic and semantic symbol resolution, handling complex generic inheritance and multi-project assembly references.

## Usage

```bash
# Build the analyzer
dotnet build dotnet-analyzer/LegacyLens.Analyzer.csproj

# Run analysis on a repository
dotnet run --project dotnet-analyzer/LegacyLens.Analyzer.csproj -- /path/to/csharp/repo output.json
```
The output JSON conforms directly to the LegacyLens `EvidenceRecord` schema and can be consumed by the MCP code intelligence server.
