# Security

Do not commit `.env` files, API keys, benchmark output containing private prompts, or customer data.

If an API key is accidentally committed:

1. Revoke the key immediately in Google AI Studio or the owning Google account.
2. Create a replacement key.
3. Remove the secret from the repository history before making the repository public.
4. Review logs, CI output, and benchmark files for accidental disclosure.

To report a vulnerability, open a private security advisory if available, or contact the maintainers through the repository's listed security contact. Please include reproduction steps, impact, and suggested remediation.

