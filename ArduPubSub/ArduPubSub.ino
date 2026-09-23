#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoBLE.h>
#include "TOPIC.h"
#include <string>
#include <vector>
/*IMPOSTAZIONI BLUETOOTH*/
// servizio per ricevere le impostazioni del wifi
BLEService dataService("19B10010-E8F2-537E-4F6C-D104768A1214"); 
//caratteristica per abilitare l'invio dei dati
BLEStringCharacteristic dataWritingCharacteristic("19B10011-E8F2-537E-4F6C-D104768A1214",BLEWrite,100);
//caratteristica per notificare che i dati sono stati inseriti
BLEByteCharacteristic dataNotifyingCharacteristic("19B10012-E8F2-537E-4F6C-D104768A1214",BLERead | BLENotify);

/* IMPOSTAZIONI WIFI*/
bool wifiConfigurato = false;
bool mqttConfigurato = false;
bool mqttAttivato = false;
String ssid = "";
String password = "";

/*IMPOSTAZIONI MQTT*/
String mqttbkr = "";
String nome = "";

WiFiClient clientWiFi;
PubSubClient client(clientWiFi);


/* Spazio per sensori e valori */
float ph = 8.0;
float livelloAcqua =  49.0;
float temperatura  = 12.0;
int check = 0;



/*Spazio per attuatori*/
void setup() {
  Serial.begin(115200);

  if(!BLE.begin()){
    Serial.println("Inizializzazione del modulo Bluetooth® Low Energy fallita"); 
    while(1);
  }else{
    Serial.println("Inizializzazione del modulo Bluetooth® Low Energy completata"); 
  }

  BLE.setLocalName("AcquarioMQTT");
  BLE.setAdvertisedService(dataService);
  
  dataService.addCharacteristic(dataWritingCharacteristic);
  dataService.addCharacteristic(dataNotifyingCharacteristic);
  BLE.addService(dataService);
  
  BLE.advertise();
  Serial.println("Acquario in attesa di connessioni"); 

  /*

  WiFi.begin(ssid,password);
  while(WiFi.status()!=WL_CONNECTED){
    delay(1000);
    Serial.println("Connessione al wifi in corso");
  }
  Serial.println("Connesso al wifi");
  client.setServer(mqttbkr.c_str(),1883);
  client.setCallback(callback);
  while(!client.connected()){
    Serial.println("CONNESSIONE AL BROKER MQTT");
    if(client.connect(nome.c_str())){
      Serial.println("CONNESSIONE EFFETTUATA");
       client.subscribe(createTopic(nome,8).c_str());
    }else{
      Serial.print("Fallito, rc = ");
      Serial.print(client.state());
      Serial.println("Riprovare"); 
      delay(5000);
    }
  }
*/ 
}

void loop() {
  if(wifiConfigurato==false && dataWritingCharacteristic.written()){
    String dati = dataWritingCharacteristic.value();
    ssid     = tokenize(dati, ',', 0);
    password = tokenize(dati, ',', 1);
    mqttbkr  = tokenize(dati, ',', 2);
    nome     = tokenize(dati, ',', 3);
    dataNotifyingCharacteristic.writeValue(1);
    wifiConfigurato = true;
    delay(500);
    BLE.disconnect();
    BLE.stopAdvertise();
    BLE.end();
    delay(500);
    WiFi.begin(ssid.c_str(),password.c_str());
    
  }
  if(WiFi.status()!= WL_CONNECTED && wifiConfigurato == true){
    Serial.println("Connessione al wifi in corso");
    delay(1000);
  }
  if(WiFi.status()==WL_CONNECTED ){
    Serial.println("Connesso al wifi");
    if(mqttConfigurato == false){
       client.setServer(mqttbkr.c_str(),1883);
       client.setCallback(callback);
       mqttConfigurato = true;
    }
    if(mqttConfigurato == true){
      if(!client.connected() && mqttAttivato == false){
        Serial.println("CONNESSIONE AL BROKER MQTT");
        if(client.connect(nome.c_str())){
          Serial.println("CONNESSIONE EFFETTUATA");
          client.subscribe(createTopic(nome,8).c_str());
          mqttAttivato = true;
        }else{
          Serial.print("Fallito, rc = ");
          Serial.print(client.state());
          Serial.println("Riprovare"); 
          delay(5000);
        }
      }
      if(mqttAttivato == true){
        if(!client.connected()){
          Serial.println("Riconnessione al broker ");
          client.connect(nome.c_str());
        }
        if(check == 0){
          client.publish("acquari/nome",nome.c_str());
        }
        client.loop();
        //client.publish("test/mqtt","Messaggio di test da arduino giga");
        publishFloatVals(client,ph,createTopic(nome,0));
        publishFloatVals(client,livelloAcqua,createTopic(nome,1));
        publishFloatVals(client,temperatura,createTopic(nome,2));


        Serial.println("Messaggio inviato"); 
        delay(5000); 

      }
    }
  }
  
  
  
}

void publishFloatVals(PubSubClient& t, float val, String topic) {
    char msg[20];
    snprintf(msg, sizeof(msg), "%1.2f", val);
    t.publish(topic.c_str(), msg);
}   

void callback(char* topic, byte* payload, unsigned int length) {
    String msg;
    for (unsigned int i = 0; i < length; i++) {
        msg += (char)payload[i];
    }

    String topicStr = String(topic);

    Serial.print("Ricevuto su: ");
    Serial.print(topicStr);
    Serial.print(" -> ");
    Serial.println(msg);

    if (topicStr == createTopic(nome,4)) {
        // pompa a immersione
       // digitalWrite(PIN_POMPAR, msg == "ON" ? HIGH : LOW);
       Serial.println("POMPA RIEMPIMENTO: " + msg);

    } else if (topicStr == createTopic(nome,5)) {
        // pompa a superficie
       // digitalWrite(PIN_POMPAS, msg == "ON" ? HIGH : LOW);
       Serial.println("POMPA SVUOTAMENTO: " + msg);

    } else if (topicStr == createTopic(nome,6)) {
        // riscaldatore
       // digitalWrite(PIN_RISC, msg == "ON" ? HIGH : LOW);
       Serial.println("RISCALDATORE: " + msg);
       
      }
}

String createTopic(String nome, int pos) {
    const char* suffix[9] = {
        "sensori/ph",
        "sensori/lvl",
        "sensori/tmp",
        "sensori/time",
        "attuatori/pr",
        "attuatori/ps",
        "attuatori/risc",
        "attuatori/luce",
        "attuatori/#"
    };

    return "acquari/" + nome + "/" + String(suffix[pos]);
}

// Estrae il campo in posizione "pos" da toTokenize, usando c come separatore.
// pos parte da 0. Ritorna "" se pos non esiste.
String tokenize(String toTokenize, char c, int pos){
  int inizio = 0;
  int campo = 0;

  for (int i = 0; i <= toTokenize.length(); i++) {
    if (i == toTokenize.length() || toTokenize[i] == c) {
      if (campo == pos) {
        return toTokenize.substring(inizio, i);
      }
      campo++;
      inizio = i + 1;
    }
  }

  return ""; // posizione non trovata
}