"""One-off: allow cross-origin GETs on the R2 media bucket.

The admin's «Обложка из кадра» draws a saved preview video onto a canvas, which
the browser only permits when the video was fetched with CORS approval
(crossOrigin=anonymous + Access-Control-Allow-Origin from the CDN). Media is
public anyway, so a wildcard read-only policy is safe. Idempotent — re-running
overwrites the same rule.

Run inside the backend container (needs R2 env):
    docker compose exec backend python -m scripts.set_r2_cors
"""
from app.core import r2
from app.core.config import settings


def main() -> None:
    if not r2.r2_enabled():
        raise SystemExit("R2 is not configured (set R2_* env vars). Aborting.")
    client = r2._get_client()
    client.put_bucket_cors(
        Bucket=settings.r2_bucket,
        CORSConfiguration={
            "CORSRules": [
                {
                    "AllowedOrigins": ["*"],
                    "AllowedMethods": ["GET", "HEAD"],
                    "AllowedHeaders": ["*"],
                    "MaxAgeSeconds": 86400,
                }
            ]
        },
    )
    print(f"CORS rule set on bucket «{settings.r2_bucket}»: GET/HEAD from any origin.")


if __name__ == "__main__":
    main()
