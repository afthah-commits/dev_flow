with open('backend/app/services/automation_engine.py', 'r') as f:
    content = f.read()

ext_code = '''
        elif action_type == "SEND_WEBHOOK":
            from app.models.webhook import WebhookEndpoint
            from app.services.webhook_dispatcher import WebhookDispatcher
            webhook_id = action.get("webhook_id")
            if webhook_id:
                webhook = db.query(WebhookEndpoint).filter(WebhookEndpoint.id == webhook_id, WebhookEndpoint.organization_id == org_id).first()
                if webhook:
                    dispatcher = WebhookDispatcher(db)
                    await dispatcher.dispatch(webhook, event_payload.get("event_type", "custom"), event_payload, execution.idempotency_key)
                    action_exec.output_data = {"webhook_id": webhook.id, "dispatched": True}
        elif action_type == "SEND_SLACK_MESSAGE":
            from app.services.providers.slack import SlackProvider
            provider = SlackProvider("mock")
            await provider.send_message(action.get("channel", "general"), action.get("message", "Auto Msg"))
            action_exec.output_data = {"slack": "sent"}
        elif action_type == "SEND_EMAIL":
            from app.services.providers.email import EmailProvider
            provider = EmailProvider({})
            await provider.send_email(action.get("to", ""), action.get("subject", ""), action.get("body", ""))
            action_exec.output_data = {"email": "sent"}
'''

if "SEND_WEBHOOK" not in content:
    content = content.replace(
        "        # More actions here...",
        "        # More actions here...\n" + ext_code
    )
    with open('backend/app/services/automation_engine.py', 'w') as f:
        f.write(content)
