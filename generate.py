from datetime import datetime as DateTime, timedelta as TimeDelta


def main():
    start = DateTime(2020, 1, 1)
    for i in range(20):
        stamp = start + (TimeDelta(minutes=30) * i)
        stamp_text = stamp.strftime("%Y-%m-%d %H:%M:%S")
        print(f"('{stamp_text}', {i % 2 == 0}),")


if __name__ == "__main__":
    main()
