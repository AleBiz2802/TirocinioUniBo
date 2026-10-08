#include "LIBRERIE.h"
#include "DEFINIZIONI.h"
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

/*PARAMETRI DA CONFIGURARE VIA APP ( TRAMITE ISCRIZIONE A TOPIC MQTT configurazione/#)*/
float phMax;
float phMin;

float livelloAcquaMin;
float livelloAcquaMax;

float livelloPhMax;
float livelloPhMin;


unsigned long campionamentoPh;
unsigned long ultimoCampionamentoPh = 0 ;
unsigned long campionamentoTmp;
unsigned long ultimoCampionamentoTmp = 0 ;
unsigned long campionamentoLivelloAcqua;
unsigned long ultimoCampionamentoLivelloAcqua = 0;
unsigned long tempo = 0 ;
int campionamentiImpostati = 0;
int check = 0;

/*valori di prova*/
float ph = 10;
float livelloAcqua =  30.0;
float temperatura  = 9.0;



/*Inizializzazione sensori*/
OneWire oneWire(TEMPERATURA);
DallasTemperature(&oneWire);

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
  dataNotifyingCharacteristic.writeValue(1);
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

  Wire.begin();
  pinMode(LIVELL0_TANICA_1,INPUT);
  pinMode(LIVELLO_ACQUA_3,INPUT);
  pinMode(LIVELLO_PH,INPUT);
  pinMode(13,OUTPUT);
  pinMode(12,OUTPUT);
  pinMode(POMPA_OUT,OUTPUT);
  pinMode(POMPA_IN,OUTPUT);
  pinMode(ILLUMINAZIONE,OUTPUT);
  pinMode(VENTOLA,OUTPUT);
  pinMode(RISCALDATORE;OUTPUT);

  digitalWrite(POMPA_IN,HIGH);
  digitalWrite(POMPA_OUT,HIGH);
  digitalWrite(VENTOLA,LOW);
  digitalWrite(ILLUMINAZIONE,HIGH); 
  digitalWrite(RISCALDATORE,HIGH);
  
}

void loop() {
  if(wifiConfigurato==false){
    BLE.poll();
    if(dataWritingCharacteristic.written()){
      String dati = dataWritingCharacteristic.value();
      ssid     = tokenize(dati, ',', 0);
      Serial.println(ssid);
      password = tokenize(dati, ',', 1);
      Serial.println(password);
      mqttbkr  = tokenize(dati, ',', 2);
      Serial.println(mqttbkr);
      nome     = tokenize(dati, ',', 3);
      Serial.println(nome);
      dataNotifyingCharacteristic.writeValue(1);
      wifiConfigurato = true;
      unsigned long t = millis();
      while (millis() - t < 500) 
      BLE.poll();

      BLE.disconnect();
      BLE.stopAdvertise();
      BLE.end();
    delay(500);
    WiFi.begin(ssid.c_str(),password.c_str());
    Serial.println(ssid.c_str());
    Serial.println(password.c_str());
    }
 
    
  }
  if(WiFi.status()!= WL_CONNECTED && wifiConfigurato == true){
  
      Serial.println("Connessione al wifi in corso");
      Serial.println(WiFi.status());
      WiFi.begin(ssid.c_str(),password.c_str());
      delay(1000);
  }
  if(WiFi.status()==WL_CONNECTED ){
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
          client.subscribe(createTopic(nome,9).c_str());
          mqttAttivato = true;
        }else{
          Serial.print("Fallito, rc = ");
          Serial.print(client.state());
          Serial.println(" Riprovare"); 
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
          check = 1;
        }
        
        //client.publish("test/mqtt","Messaggio di test da arduino giga");
       
        publishFloatVals(ph,0,ultimoCampionamentoPh,campionamentoPh);
        publishFloatVals(livelloAcqua,1,ultimoCampionamentoLivelloAcqua,campionamentoLivelloAcqua);
        publishFloatVals(temperatura,2,ultimoCampionamentoTmp,campionamentoTmp);
      
        client.loop();
       // delay(5000);
      }
    }
  }
  
  
  
}

void publishFloatVals(PubSubClient& t, float val, String topic) {
    char msg[20];
    snprintf(msg, sizeof(msg), "%1.2f", val);
    t.publish(topic.c_str(), msg);
}   

void publishFloatVals(float val, int n, unsigned long &ultimoInvio, unsigned long intervallo){
  //unsigned long tempoPrev = 0;
  if(intervallo!=0){
      if(millis()-ultimoInvio>=intervallo){
      ultimoInvio= millis();
      publishFloatVals(client,val,createTopic(nome,n));
       Serial.println("Messaggio inviato"); 
    }
  }
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
    } else if( topicStr ==  createTopic(nome,10)){
        int val = msg.toInt();
        campionamentoPh = 1000*val;
        Serial.print("Campionamento ph : ");Serial.print(campionamentoPh);Serial.print("\n");
    } else if (topicStr == createTopic(nome,11)){
        int val = msg.toInt();
        campionamentoLivelloAcqua = 1000*val;
        Serial.print("Campionamento acqua : ");Serial.print(campionamentoLivelloAcqua);Serial.print("\n");
    } else if(topicStr == createTopic(nome,12)){
        int val = msg.toInt();
        campionamentoTmp = 1000*val;
        Serial.print("Campionamento temperatura: ");Serial.print(campionamentoTmp);Serial.print("\n");
    }
}

String createTopic(String nome, int pos) {
    const char* suffix[13] = {
        "sensori/ph", 
        "sensori/lvl",
        "sensori/tmp",
        "sensori/time",
        "attuatori/pr",
        "attuatori/ps",
        "attuatori/risc",
        "attuatori/luce",
        "attuatori/#",
        "configurazione/#",
        "configurazione/temporizzazione/tempoPh",
        "configurazione/temporizzazione/tempoLivelloAcqua",
        "configurazione/temporizzazione/tempoTemperatura"
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


