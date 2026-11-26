import getpass

import config_store


def main() -> None:
    resend_key = getpass.getpass("Resend API key (hidden, Enter to skip): ").strip()
    if resend_key:
        current = config_store.get_email_settings()
        sender = input(f"From address [{current['sender'] or 'onboarding@resend.dev'}]: ").strip()
        config_store.save_email_settings({"api_key": resend_key, "sender": sender or current["sender"]})
        print("Resend settings saved.")

    simgate_key = getpass.getpass("SimGate API key (hidden, Enter to skip): ").strip()
    if simgate_key:
        current = config_store.get_sms_settings()
        device = input(f"SimGate device ID [{current['device_id']}]: ").strip() or current["device_id"]
        config_store.save_sms_settings({"api_key": simgate_key, "device_id": device})
        print("SimGate settings saved.")

    print(f"Config file: {config_store.CONFIG_PATH}")


if __name__ == "__main__":
    main()
