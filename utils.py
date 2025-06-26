import dataclasses
import datetime
import decimal
import difflib
import enum
import json
import logging
import os
import tempfile
from typing import Any, Callable, Optional


logging.basicConfig(level=logging.WARNING)


def serialize(obj: Any) -> Any:
    """Recursively serialize an object for JSON dumping, including dataclasses, Pydantic, etc"""
    if dataclasses.is_dataclass(obj):
        return {f.name: serialize(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
    if hasattr(obj, "model_dump"):  # Pydantic v2
        return serialize(obj.model_dump())
    if hasattr(obj, "dict"):  # Pydantic v1
        return serialize(obj.dict())
    if isinstance(obj, (list, tuple, set)):
        return [serialize(item) for item in obj]
    if isinstance(obj, dict):
        return {serialize(k): serialize(v) for k, v in obj.items()}
    if isinstance(obj, enum.Enum):
        return obj.value
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, decimal.Decimal):
        return str(obj)
    if hasattr(obj, "__dict__") and not isinstance(obj, type):
        # Exclude private attributes
        return {k: serialize(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    if isinstance(obj, str):
        # Optional: Only decode as dict or list if string starts with '{' or '['
        s = obj.strip()
        if s.startswith("{") or s.startswith("["):
            try:
                return json.loads(s)
            except Exception:
                pass
        return obj
    if isinstance(obj, (int, float, bool)) or obj is None:
        return obj
    return str(obj)  # fallback for everything else



def to_json(input_data: Any, file_path: str = None) -> str:
    data = serialize(input_data)
    json_str = json.dumps(data, indent=4)
    if file_path:
        with open(file_path, "w") as f:
            f.write(json_str)
            logging.info(f"JSON data saved to {file_path}")
        return file_path
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        tmp.write(json_str)
        logging.info(f"JSON data saved to {tmp.name}")
        return tmp.name


def compare_objects_diff(
    obj1: Any,
    obj2: Any,
    serialize_func: Optional[Callable[[Any], dict]] = None,
    output_dir: str = "/Users/sajid/tmp",
    filename: str = "object_diff.html"
) -> str:
    """
    # Using some question serializer
    # from dataclasses import dataclass, asdict
    # compare_objects_as_dicts(obj1, obj2, serialize=asdict)
    # or  pydantic’s dict(),
    """
    if serialize_func is None:
        serialize_func = serialize

    dict1 = serialize_func(obj1)
    dict2 = serialize_func(obj2)
    json1 = json.dumps(dict1, indent=2, sort_keys=True)
    json2 = json.dumps(dict2, indent=2, sort_keys=True)

    lines1 = json1.splitlines()
    lines2 = json2.splitlines()

    differ = difflib.HtmlDiff(tabsize=2, wrapcolumn=80)
    html_report = differ.make_file(lines1, lines2, fromdesc="Object 1", todesc="Object 2")

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_report)

    print(f"Diff report saved at: {output_path}")
    return output_path
