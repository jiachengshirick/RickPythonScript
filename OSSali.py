from aliyunsdkcore.client import AcsClient
from aliyunsdkoss.request.v20181015 import GetObjectRequest
client = AcsClient('<AccessKey>', '<Secret>', 'cn-hangzhou')
req = GetObjectRequest() \
  .set_BucketName('my-bucket') \
  .set_Key('path/to/image.jpg')
response = client.do_action_with_exception(req)
with open('/tmp/image.jpg', 'wb') as f:
  f.write(response)