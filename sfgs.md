
class AvatarPresignResponse(BaseModel):
    url: str
    fields: dict[str, str]
    key: str


key + /original
<?xml version="1.0" encoding="UTF-8"?>
<Error><Code>MalformedPOSTRequest</Code><Message>The body of your POST request is not well-formed multipart/form-data. (The name of the uploaded key is missing)</Message><BucketName>profiles</BucketName><Resource>/profiles</Resource><RequestId>189ECF8F141012BE</RequestId><HostId>dd9025bab4ad464b049177c95eb6ebf374d3b3fd1af9251148b658df7ac2e3e8</HostId></Error>



