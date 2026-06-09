from django.test import Client, TestCase

class HealthTest(TestCase):
    def test_health(self):
        client = Client()
        resp = client.get('/health/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {'status': 'ok'})
