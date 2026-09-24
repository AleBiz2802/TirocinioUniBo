import asyncio
from bleak import BleakScanner, BleakClient

NAME        = "AcquarioMQTT"
WRITE_UUID  = "19B10011-E8F2-537E-4F6C-D104768A1214"
NOTIFY_UUID = "19B10012-E8F2-537E-4F6C-D104768A1214"

async def main():
    ack_event = asyncio.Event()

    def on_notify(sender, data):
        print(f"Notifica ricevuta: {list(data)}")
        if data and data[0] == 1:
            ack_event.set()

    print("Scansione...")
    device = await BleakScanner.find_device_by_name(NAME, timeout=15)
    if device is None:
        print("Dispositivo non trovato")
        return
    print(f"Trovato: {device.name} ({device.address})")

    try:
        async with BleakClient(device, timeout=20) as client:
            print("Connesso al dispositivo")
            await client.start_notify(NOTIFY_UUID, on_notify)
            ssid = input("inserisci il nome della rete").strip()
            password = input("inserisci la password della rete").strip()
            mqtt_broker = input("inserisci l'indirizzo del broker MQTT").strip()
            nome = input("inserisci il nome dell'acquario").strip()
            payload = f"{ssid},{password},{mqtt_broker},{nome}"
            await client.write_gatt_char(WRITE_UUID, payload.encode(), response=True)
            print("Dati inviati, attendo ACK...")

            await asyncio.wait_for(ack_event.wait(), timeout=10)
            print("Configurazione confermata")
    except asyncio.TimeoutError:
        print("Nessun ACK ricevuto")
    except Exception as e:
        # l'Arduino si disconnette da solo dopo l'ACK, può dare errore in chiusura
        print(f"Chiusura connessione: {e}")

asyncio.run(main())