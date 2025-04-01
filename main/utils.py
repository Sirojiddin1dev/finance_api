import requests
from django.conf import settings
import json
import logging

# Logger yaratish
logger = logging.getLogger(__name__)


class EskizSMS:
    def __init__(self):
        self.email = settings.ESKIZ_EMAIL
        self.password = settings.ESKIZ_PASSWORD
        self.base_url = "https://notify.eskiz.uz/api"
        self._token = None

    def _login(self):
        """Eskiz.uz tizimiga kirish va token olish"""
        url = f"{self.base_url}/auth/login"
        data = {
            "email": self.email,
            "password": self.password
        }
        try:
            logger.info(f"Eskiz.uz ga ulanish: {url}")
            response = requests.post(url, json=data)
            logger.info(f"Login javobi: Status={response.status_code}, Body={response.text}")

            if response.status_code == 200:
                response_data = response.json()
                self._token = response_data.get('data', {}).get('token')
                if self._token:
                    logger.info("Token muvaffaqiyatli olindi")
                    return True
                else:
                    logger.error("Token topilmadi")
                    return False
            else:
                logger.error(f"Login xatosi: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Login paytida xatolik: {str(e)}")
            return False

    def _get_headers(self):
        """So'rov uchun headers"""
        if not self._token:
            logger.info("Token mavjud emas, qayta login qilinmoqda")
            self._login()

        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json"
        }
        logger.debug(f"Headers: {headers}")
        return headers

    def send_sms(self, phone_number, message):
        """SMS yuborish"""
        url = f"{self.base_url}/message/sms/send"

        # Telefon raqamini to'g'ri formatga keltirish
        if phone_number.startswith('+'):
            phone_number = phone_number[1:]

        data = {
            "mobile_phone": phone_number,
            "message": message,
            "from": "4546"
        }

        logger.info(f"SMS yuborilmoqda: Tel={phone_number}, Xabar={message}")
        logger.debug(f"To'liq so'rov ma'lumotlari: URL={url}, Data={data}")

        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=data
            )

            logger.info(f"SMS yuborish javobi: Status={response.status_code}, Body={response.text}")

            if response.status_code == 200:
                response_data = response.json()
                if response_data.get('status') == 'success':
                    logger.info("SMS muvaffaqiyatli yuborildi")
                    return True, "SMS muvaffaqiyatli yuborildi"

                error_msg = response_data.get('message', 'Noma\'lum xatolik')
                logger.error(f"SMS yuborishda API xatoligi: {error_msg}")
                return False, error_msg

            elif response.status_code == 401:
                logger.warning("Token eskirgan, qayta login qilinmoqda")
                if self._login():
                    logger.info("Qayta urinish...")
                    return self.send_sms(phone_number, message)

                logger.error("Qayta login qilish muvaffaqiyatsiz")
                return False, "Autentifikatsiya xatosi"

            logger.error(f"Kutilmagan status kod: {response.status_code}")
            return False, f"Xatolik yuz berdi: {response.status_code} - {response.text}"

        except requests.exceptions.ConnectionError as e:
            error_msg = f"Ulanish xatosi: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

        except requests.exceptions.Timeout as e:
            error_msg = f"So'rov vaqti tugadi: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

        except Exception as e:
            error_msg = f"Kutilmagan xatolik: {str(e)}"
            logger.error(error_msg)
            return False, error_msg


def send_sms_eskiz(phone_number, message):
    """
    Eskiz.uz orqali SMS yuborish

    Args:
        phone_number (str): Telefon raqami (998XXXXXXXXX formatida)
        message (str): Yuborilishi kerak bo'lgan xabar

    Returns:
        bool: SMS yuborildi yoki yuborilmadi
    """
    eskiz = EskizSMS()
    success, error_message = eskiz.send_sms(phone_number, message)

    if not success:
        logger.error(f"SMS yuborib bo'lmadi: {error_message}")

    return success