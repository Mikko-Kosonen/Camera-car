# Camera-car

Kouluprojekti, jossa minun tehtäväni oli käyttöjärjestelmän rakentaminen Raspberry Pi:n avulla. 

Raspberry Pi:llä käynnistetään Apache2 ohjelmisto, joka tekee Raspberry Pi:stä verkkopalvelimen lähiverkkoon. Lisäksi Raspberry Pi:lle käynnistetään raspi_auto.py ohjelma, joka huolehtii käyttäjän lähettämän datan käsittelystä, USB-kameran ja GPIO-pinnien käytöstä, sekä ohjauskomentojen lähettämisestä Arduinolle USB:n kautta. 

Käyttäjä yhdistää päätelaitteensa samaan lähiverkkoon Raspberry Pi:n kanssa ja kirjoittaa verkkoselaimeen Pi:n IP-osoitteen. Avautuvassa näkymässä on joystick auton ohjaukseen sekä napit kameran käyttöä varten. Sivun yläosassa on kaksi ruutua, joista alemmassa näkyy live-video kamerasta ja ylemmässä ruudussa voidaan selata otettuja kuvia.
