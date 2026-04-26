# bazos-reupload

A Python script to delete and upload all Bazoš ads again to make them more relevant

## Usage

> [!IMPORTANT]  
> As of April 2026, Bazoš has implemented a new security measure that requires users to verify their bank accounts before interacting with most of the website's features, including ad management. This script will not work until you have completed the bank account verification process on Bazoš for your phone number by sending 1 CZK to their bank account with your phone number in the transaction note.

- Install Python dependencies
  ```sh
  pip install PyYAML requests pyquery colorama
  ```
- Run the script using Python
  ```sh
  py app.py
  ```
- On the first run, you will be asked for 3 things
  - The e-mail address used on Bazoš
  - The phone number used on Bazoš
  - The password used for editing and deleting your Bazoš ads
- Type in the recieved SMS code
- Profit!

> [!NOTE]  
> All these credentials will be saved into a local `config.yaml` file, so that you don't have to provide them every time you run this script.

> [!CAUTION]
> Running this script too often may get you banned from Bazoš in one way or another. I've been using it twice a week without any issues so far. You have been warned.
