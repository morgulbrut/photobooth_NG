from webdav3.client import Client
options = {
 'webdav_hostname': "https://shared03.opsone-cloud.ch/remote.php/dav/files/tillo.bosshart@gmail.com/",
 'webdav_login':    "tillo.bosshart@gmail.com",
 'webdav_password':  "82Z*0!fHs0rV5hDiTH6I"

}
client = Client(options)
# client.verify = False # To not check SSL certificates (Default = True)
# client.session.proxies(...) # To set proxy directly into the session (Optional)
# client.session.auth(...) # To set proxy auth directly into the session (Optional)
client.mkdir('test')

client.upload_sync(remote_path="test/test2.png", local_path="output/merged_image.png")


# https://shared03.opsone-cloud.ch/index.php/s/NaR737LsRRZt2it