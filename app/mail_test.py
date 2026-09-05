import argparse

from app.email import send_result_email


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a DearFuture test letter")
    parser.add_argument("recipient", help="Email address that should receive the test")
    args = parser.parse_args()

    result = send_result_email(
        recipient=args.recipient,
        question="这是一封来自 DearFuture 的试投信。",
        outcome="uncertain",
        summary="小蜗牛已经找到了通往你邮箱的路。",
        letter="邮件配置成功。以后，当约定的日子到来，真正的未来回信也会沿着这条路送达。",
        public_url=None,
    )
    if result.status != "sent":
        raise SystemExit(f"Test email was not sent: {result.error or result.status}")
    print("Test email sent successfully.")


if __name__ == "__main__":
    main()
