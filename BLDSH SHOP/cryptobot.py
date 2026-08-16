import aiohttp

from config import CRYPTO_TOKEN


API_URL = "https://pay.crypt.bot/api"



async def create_invoice(
    rubles,
    asset="USDT"
):

    # Курс USDT → рубли:
    # 1 USDT ≈ 78 рублей
    if asset == "USDT":

        crypto_amount = round(
            rubles / 78,
            2
        )

    else:

        crypto_amount = rubles


    data = {
        "asset": asset,
        "amount": crypto_amount
    }


    headers = {
        "Crypto-Pay-API-Token": CRYPTO_TOKEN
    }


    async with aiohttp.ClientSession() as session:

        async with session.post(

            f"{API_URL}/createInvoice",

            headers=headers,

            json=data

        ) as response:


            result = await response.json()


            print("CRYPTOBOT RESPONSE:")
            print(result)



            if result.get("ok"):

                return result["result"]


            return None
async def check_invoice(invoice_id):

    url = "https://pay.crypt.bot/api/getInvoices"

    headers = {
        "Crypto-Pay-API-Token": CRYPTO_TOKEN
    }

    params = {
        "invoice_ids": str(invoice_id)
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=headers,
                params=params
            ) as response:
                data = await response.json()

                if not data.get("ok"):
                    return None

                invoices = data.get("result", {}).get("items", [])

                if not invoices:
                    return None

                return invoices[0]["status"]
    except Exception as e:
        print(f"CRYPTOBOT check_invoice error: {e}")
        return None