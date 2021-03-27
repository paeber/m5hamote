import urequests
import json

class HomeAssistant:
  def __init__(self, url, token):
    self.url = url
    self.token = token
    self.headers = {'Authorization': str('Bearer '+ self.token),'content-type':'application/json'}

  def getJson(self, entity_id):
    req = urequests.request(method='GET', url=(self.url + str('/api/states/') + entity_id), headers={'Authorization':((str('Bearer ') + self.token)),'content-type':'application/json'})
    return json.loads(req.text)

  def getState(self, entity_id):
    return self.getJson(entity_id)['state']

  def call(self, entity_id, service, data={}):
    domain, entity = entity_id.split(".", 1)
    target = str(self.url) + "/api/services/" + str(domain) + "/" + str(service)
    payload = {"entity_id": entity_id}
    for key in data:
      payload[key] = data[key]
    req = urequests.request(method='POST', url=str(target),json=payload, headers=self.headers)
