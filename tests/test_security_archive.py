import zipfile

import pytest

from backend.app.core.security import SecurityValidationError, validate_and_extract_zip


def test_safe_zip_extraction(tmp_path):
    zip_path = tmp_path / "valid.zip"
    extract_dir = tmp_path / "extracted"

    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("Orders/OrdersController.cs", "public class OrdersController {}")
        z.writestr("appsettings.json", "{}")

    count, files = validate_and_extract_zip(zip_path, extract_dir)
    assert count == 2
    assert (extract_dir / "Orders" / "OrdersController.cs").exists()

def test_rejects_path_traversal_attack(tmp_path):
    zip_path = tmp_path / "evil_traversal.zip"
    extract_dir = tmp_path / "extracted"

    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("../../../etc/evil.cs", "malicious payload")

    with pytest.raises(SecurityValidationError) as exc_info:
        validate_and_extract_zip(zip_path, extract_dir)
    assert "traversal" in str(exc_info.value).lower()

def test_ignores_dangerous_binary_files(tmp_path):
    zip_path = tmp_path / "with_exe.zip"
    extract_dir = tmp_path / "extracted"

    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("malware.exe", "binary payload")
        z.writestr("OrderService.cs", "public class OrderService {}")

    count, files = validate_and_extract_zip(zip_path, extract_dir)
    assert count == 1
    assert not (extract_dir / "malware.exe").exists()
    assert (extract_dir / "OrderService.cs").exists()
