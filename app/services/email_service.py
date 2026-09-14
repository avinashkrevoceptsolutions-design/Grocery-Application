
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import settings


class EmailService:

    async def send_email(self, to_email, subject, body):
        if isinstance(to_email, str):
            recipients = [to_email]
        else:
            recipients = to_email

        message = MIMEMultipart()
        message["From"] = settings.MAIL_FROM or settings.SMTP_USERNAME
        message["To"] = ", ".join(recipients)
        message["Subject"] = subject

        message.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(
            settings.SMTP_HOST,
            settings.SMTP_PORT
        )

        server.starttls()
        server.login(
            settings.SMTP_USERNAME,
            settings.SMTP_PASSWORD
        )

        server.sendmail(
            settings.MAIL_FROM or settings.SMTP_USERNAME,
            recipients,
            message.as_string()
        )

        server.quit()

    async def send_order_notifications(self, customer, order):
        order_items = []

        for item in order["items"]:
            order_items.append(
                f"- {item['name']}: "
                f"Quantity {item['quantity']}, "
                f"Price {item['price']:.2f}, "
                f"Total {item['total_price']:.2f}"
            )

        order_details = (
            f"Order ID: {order['id']}\n"
            f"Order date: {order['created_at']}\n"
            f"Status: {order['status']}\n\n"
            f"Products:\n"
            f"{chr(10).join(order_items)}\n\n"
            f"Total amount: {order['total_amount']:.2f}"
        )

        customer_body = (
            "Your order has been placed.\n\n"
            "Order details:\n"
            f"{order_details}"
        )

        await self.send_email(
            customer["email"],
            "Your order has been placed",
            customer_body
        )

    
        customer_name = (
            f"{customer.get('first_name', '')} "
            f"{customer.get('last_name', '')}"
        )

        admin_body = (
            "A new order has been placed.\n\n"
            "Customer details:\n"
            f"Customer ID: {customer.get('id')}\n"
            f"Name: {customer_name}\n"
            f"Email: {customer.get('email')}\n"
            f"Username: {customer.get('username')}\n"
            f"Phone: {customer.get('phone_number')}\n"
            f"Role: {customer.get('role')}\n\n"
            "Order details:\n"
            f"{order_details}"
        )

        await self.send_email(
            settings.ADMIN_EMAIL,
            "Order has been placed",
            admin_body
        )


email_service = EmailService()