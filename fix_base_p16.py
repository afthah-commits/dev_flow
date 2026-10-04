with open('backend/app/db/base.py', 'r') as f:
    content = f.read()

import_str = "from app.models.integration import Integration, IntegrationCredential, IntegrationLog\nfrom app.models.webhook import WebhookEndpoint, WebhookDelivery\nfrom app.models.api_key import APIKey\n"
if "from app.models.api_key" not in content:
    content += import_str
    with open('backend/app/db/base.py', 'w') as f:
        f.write(content)
