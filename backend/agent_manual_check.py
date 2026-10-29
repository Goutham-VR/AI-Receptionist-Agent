from app.agent import receptionist_agent


def main():
    print("AI Receptionist Agent")
    print("=" * 35)

    while True:
        user_message = input("\nYou: ").strip()

        if user_message.lower() in {"exit", "quit"}:
            print("Receptionist: Goodbye!")
            break

        if not user_message:
            continue

        print("\nThinking...")

        try:
            response = receptionist_agent(user_message)
            print("\nReceptionist:", response)

        except Exception as error:
            print("\nAgent error:", str(error))


if __name__ == "__main__":
    main()