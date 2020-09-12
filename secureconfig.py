import yaml
import gnupg
import util
import getpass


class SecureConfig(object):

    def __init__(self):
        """
        load gpg key store
        """
        # must set use_agent to True. otherwise users have to enter passphrase every time.
        self.gpg = gnupg.GPG(use_agent=True)

    def encrypt(self, plain_file: str, encrypted_file: str, recipients: list):
        """
        Encrypt the configuration file with public keys of all CeR members

        :param plain_file:
        :param encrypted_file:
        :param recipients:
        :return:
        """
        with open(plain_file, 'rb') as f:
            result = self.gpg.encrypt_file(
                file=f,
                always_trust=True,
                recipients=recipients,
                output=encrypted_file
            )
            return result.ok

    def decrypt(self, encrypted_file: str) -> dict:
        """
        Decrypt the config file with private key. May ask for password

        :param encrypted_file:
        :return:
        """

        keys = self.gpg.list_keys(secret=True)
        if len(keys) < 1:
            raise Exception('No private key found in gpg store, please run "eres init"')

        with open(encrypted_file, 'r') as f:
            enc_text = f.read()
            # print(enc_text)
            status = self.gpg.decrypt(enc_text, always_trust=True)
            while not status.ok:
                passphrase = getpass.getpass(prompt='Please enter you gpg passphrase:')
                status = self.gpg.decrypt(enc_text, always_trust=True, passphrase=passphrase)

            # assume the decryption is successful
            return yaml.safe_load(str(status))


if __name__ == '__main__':
    sc = SecureConfig()
    sc.encrypt('config.yml', util.secure_config_file, sc.gpg.list_keys(secret=True)[0]['uids'])
