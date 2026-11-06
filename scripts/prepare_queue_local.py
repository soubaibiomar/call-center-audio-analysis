"""Create private local queue files exclusively; never rotate existing credentials."""

import argparse
import json
import secrets
import subprocess
from pathlib import Path


def write_new(path: Path, value: str) -> None:
    if not path.exists():
        with path.open("x", encoding="utf-8") as stream:
            stream.write(value)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap-storage", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = root / ".local"
    folder.mkdir(exist_ok=True)
    for name in (
        "redis_password",
        "s3_root_user",
        "s3_root_password",
        "s3_access_key",
        "s3_secret_key",
    ):
        write_new(folder / name, secrets.token_urlsafe(32))
    password = (folder / "redis_password").read_text().strip()
    write_new(
        folder / "redis.conf",
        "bind 0.0.0.0\nprotected-mode yes\nappendonly yes\n"
        f"dir /data\nrequirepass {password}\nmaxmemory 128mb\nmaxmemory-policy noeviction\n",
    )
    values = dict(
        redis_url=f"redis://:{password}@redis:6379/0",
        endpoint_url="http://object-store:9000",
        access_key=(folder / "s3_access_key").read_text().strip(),
        secret_key=(folder / "s3_secret_key").read_text().strip(),
        tenants=["00000000-0000-0000-0000-000000000001"],
    )
    write_new(folder / "queue_config.json", json.dumps(values, indent=2))
    host = dict(
        values,
        redis_url=f"redis://:{password}@127.0.0.1:16379/0",
        endpoint_url="http://127.0.0.1:19100",
    )
    write_new(folder / "queue_host.json", json.dumps(host, indent=2))
    print("Private queue files verified; existing files preserved")
    if args.bootstrap_storage:
        script = (root / "infrastructure/compose/bootstrap-storage.sh").read_bytes()
        # Native PowerShell text pipes append CRLF; pass normalized bytes directly.
        subprocess.run(
            [
                "docker",
                "compose",
                "--env-file",
                ".env.docker",
                "-f",
                "compose.local.yml",
                "-f",
                "infrastructure/compose/queue.local.yml",
                "exec",
                "-T",
                "object-store",
                "/bin/sh",
                "-s",
            ],
            cwd=root,
            input=script.replace(b"\r\n", b"\n"),
            check=True,
        )


if __name__ == "__main__":
    main()
