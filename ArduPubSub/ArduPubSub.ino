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
String ssid = "";
String password = "";

/*IMPOSTAZIONI MQTT*/
String mqttbkr = "";
String nome = "";
bool mqttConfigurato = false;
bool mqttAttivato = false;
bool check = false;

WiFiClient clientWiFi;
PubSubClient client(clientWiFi);

/*PARAMETRI DA CONFIGURARE VIA APP ( TRAMITE ISCRIZIONE A TOPIC MQTT configurazione/#)*/
unsigned long campionamentoPh;
unsigned long ultimoCampionamentoPh = 0 ;
unsigned long campionamentoTmp;
unsigned long ultimoCampionamentoTmp = 0 ;
unsigned long campionamentoLivelloAcqua;
unsigned long ultimoCampionamentoLivelloAcqua = 0;
unsigned long tempo = 0 ;
int campionamentiImpostati = 0;


/*valori di prova*/
float ph = 10;
float livelloAcqua =  30.0;
float temperatura  = 9.0;
int valRiempimento;
/*Campionamenti da sensori*/
float phVal;
float tmpVal;
float lvlAcquaVal;

/*Valori di stato degli attuatori*/
bool OUT_PUMP = HIGH,IN_PUMP=HIGH,HEAT=HIGH,LIGHT=HIGH,FILTER=HIGH;
bool limit1=true,limit2=true,limit3=true,campionaUltrasuoni,configInizio;
int ultraVal =0;
int empty,full;
/*Inizializzazione sensori*/
OneWire oneWire(TEMPERATURA);
DallasTemperature sensore(&oneWire);
DeviceAddress indirizzo;

/*Spazio per attuatori*/
void setup() {

  Serial.begin(115200);
  if(!BLE.begin()){
    Serial.println("Inizializzazione del modulo Bluetooth® Low Energy fallita"); 
    while(1);
  }else{
    Serial.println("Inizializzazione del modulo Bluetooth® Low Energy completata"); 
  }
  sensore.begin();
  Serial.print("Sensori di temperatura trovati: ");
  Serial.println(sensore.getDeviceCount());
  BLE.setLocalName("AcquarioMQTT");
  BLE.setAdvertisedService(dataService);
  
  dataService.addCharacteristic(dataWritingCharacteristic);
  dataService.addCharacteristic(dataNotifyingCharacteristic);
  BLE.addService(dataService);
  
  BLE.advertise();
  Serial.println("Acquario in attesa di connessioni"); 
  dataNotifyingCharacteristic.writeValue(1);

  Wire.begin();

  pinMode(LIVELLO_TANICA_1,INPUT);
  pinMode(LIVELLO_ACQUA_3,INPUT);
  pinMode(LIVELLO_PH,INPUT);
  pinMode(13,OUTPUT);
  pinMode(12,OUTPUT);
  pinMode(POMPA_OUT,OUTPUT);
  pinMode(POMPA_IN,OUTPUT);
  pinMode(ILLUMINAZIONE,OUTPUT);
  pinMode(VENTOLA,OUTPUT);
  pinMode(RISCALDATORE,OUTPUT);

  pinMode(TRIGGER,OUTPUT);
  pinMode(ECHO,INPUT);

  digitalWrite(POMPA_IN,HIGH);
  digitalWrite(POMPA_OUT,HIGH);
  digitalWrite(VENTOLA,HIGH);
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
          client.subscribe(createTopic(nome,14).c_str());
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
          client.subscribe(createTopic(nome,8).c_str());
          client.subscribe(createTopic(nome,9).c_str());
          client.subscribe(createTopic(nome,14).c_str());
        }
        if(check == false){
          client.publish("acquari/nome",nome.c_str(),true);
          check = true;
        }
        int checkLivello = digitalRead(LIVELLO_ACQUA_3);
        if(campionaUltrasuoni){
          if(checkLivello==0){
            if(limit1 == true){
              if(limit3 == true){
                client.publish(("stato/" + nome).c_str(), "CONFIGURAZIONE", true);
                limit3 = false;
              }
               ultraVal = getLevel();
              if(ultraVal>0){
                empty = ultraVal;
                publishSensorValues(client, (float)empty, "acquari/" + nome + "/ultraSuoni/minLvl",true);
                Serial.print("Inviato valore di empty: "); Serial.println(empty);
                limit1 = false;
                configInizio = LOW; 
              }
              else{
              Serial.println("Riprovo a campionare il valore di empty");
              ultraVal = getLevel();
              configInizio = HIGH;
             }
            }
            digitalWrite(POMPA_IN,configInizio); 
          }else{
            digitalWrite(POMPA_IN,HIGH);
            if(limit2==true){
              ultraVal = getLevel();
              if(ultraVal<empty && ultraVal>=0){
                full = ultraVal;
                publishSensorValues(client, (float)full, "acquari/" + nome + "/ultraSuoni/maxLvl",true);
                Serial.print("Inviato valore di full: "); Serial.println(full);
                limit2 = false;
                campionaUltrasuoni = false;
                client.publish(("stato/" + nome).c_str(), "OK", true);
              }else{
                Serial.println("Riprovo a campionare il valore di full");
                ultraVal = getLevel();
              }
            }
          }
        }

        //LETTURA DELLE GRANDEZZE
        if(limit2 == false ){
          sensore.requestTemperatures();

          if (sensore.getAddress(indirizzo, 0) && sensore.isConnected(indirizzo)) {
            tmpVal = sensore.getTempC(indirizzo);
          } else {
            Serial.println("Sensore 1 non trovato");
          if (sensore.getAddress(indirizzo, 1) && sensore.isConnected(indirizzo)) {
            tmpVal = sensore.getTempC(indirizzo);
          } else {
            Serial.println("Sensore 2 non trovato");
            tmpVal = -127;
          }
        }
      
        phVal = getPhVal();
        valRiempimento = getLevel();
        publishSensorValues(phVal,0,ultimoCampionamentoPh,campionamentoPh,false);
        publishSensorValues(valRiempimento,1,ultimoCampionamentoLivelloAcqua,campionamentoLivelloAcqua,false);
        publishSensorValues(tmpVal,2,ultimoCampionamentoTmp,campionamentoTmp,false);
      }
      if(!campionaUltrasuoni){
        digitalWrite(POMPA_OUT,OUT_PUMP);
        digitalWrite(POMPA_IN,IN_PUMP);
        digitalWrite(RISCALDATORE,HEAT);
        digitalWrite(FILTRO,FILTER);
        digitalWrite(ILLUMINAZIONE,LIGHT);
      }
      client.loop();
     }
   }
  }
}

void publishSensorValues(PubSubClient& t, float val, String topic, bool retained) {
    char msg[20];
    snprintf(msg, sizeof(msg), "%1.2f", val);
    t.publish(topic.c_str(), msg,retained);
}   

void publishSensorValues(float val, int n, unsigned long &ultimoInvio, unsigned long intervallo,bool retained){
  
  if(intervallo!=0){
      if(millis()-ultimoInvio>=intervallo){
      ultimoInvio= millis();
      publishSensorValues(client,val,createTopic(nome,n),retained);
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
      if(msg == "HIGH")
       IN_PUMP = LOW;
      else
       IN_PUMP = HIGH;
       Serial.println("POMPA RIEMPIMENTO: " + msg);

    } else if (topicStr == createTopic(nome,5)) {
  
         if(msg == "HIGH")
          OUT_PUMP = LOW;
          else
          OUT_PUMP = HIGH;
       Serial.println("POMPA SVUOTAMENTO: " + OUT_PUMP);

    } else if (topicStr == createTopic(nome,6)) {
         if(msg == "HIGH")
          HEAT = LOW;
          else
          HEAT = HIGH;
       
       Serial.println("RISCALDATORE: " + msg);
    } else if(topicStr == createTopic(nome,7)){
        if(msg == "HIGH")
          LIGHT = HIGH;
          else
          LIGHT = LOW;
      Serial.println("LUCI: "+msg);
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
    } else if(topicStr == createTopic(nome,13)){
        if(msg == "HIGH")
          FILTER = LOW;
          else
          FILTER = HIGH;
    } else if (topicStr == createTopic(nome,14)){
      if(msg == "attiva")
        campionaUltrasuoni = true;
    }
}

String createTopic(String nome, int pos) {
    const char* paths[16] = {
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
        "configurazione/temporizzazione/tempoTemperatura",
        "attuatori/filtro",
        "campionaUltraSuoni",
        "UltraSuoniCampionati"
    };

    return "acquari/" + nome + "/" + String(paths[pos]);
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


float getPhVal(){
  int campioni[10];

  for(int i = 0; i < 10; i++){
    campioni[i] = analogRead(LIVELLO_PH);
  }

  // ordinamento crescente
  for(int i = 0; i < 10 - 1; i++){
    for(int j = i + 1; j < 10; j++){
      if(campioni[i] > campioni[j]){
        int temp = campioni[i];
        campioni[i] = campioni[j];
        campioni[j] = temp;
      }
    }
  }

  // media escludendo i 2 più bassi e i 2 più alti
  long somma = 0;
  for(int i = 2; i < 10 - 2; i++){
    somma += campioni[i];
  }
  float media = (float)somma / (10 - 4);

  const float VREF = 3.3;
  const float ADC_MAX = 1023.0; 
  float phVolt = media * VREF / ADC_MAX;

  float ph = -5.54 * phVolt + 20.84;  
  return fabs(ph);
}


int getLevel() {
    digitalWrite(TRIGGER, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIGGER, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIGGER, LOW);

    long durata = pulseIn(ECHO, HIGH, 30000);   
    if (durata == 0){
      return -1; 
    }                    
    return (int)(durata * 0.034 / 2);    
}
