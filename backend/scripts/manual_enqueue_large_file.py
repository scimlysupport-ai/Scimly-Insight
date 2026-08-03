from app.workers.tasks import process_large_file


def main() -> None:
    result = process_large_file.delay(43)
    print("task id", result.id)
    print("status", result.status)
    try:
        res = result.get(timeout=20, propagate=False)
        print("result", res)
    except Exception as exc:
        print("result exception", type(exc).__name__, exc)
    print("final status", result.status)


if __name__ == "__main__":
    main()
