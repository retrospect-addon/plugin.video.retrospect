--------------------------------------------------------------------------------------------
 Retrospect 3.x.x
--------------------------------------------------------------------------------------------
 Contents
 0. License
 1. Introduction
 2. Changelog
 3. Skinning
 4. Known Issues
 4a.Some channels are not working? How come?
 5. Acknowledgements
 6. Donations
--------------------------------------------------------------------------------------------
 
--------------------------------------------------------------------------------------------
 0. License
--------------------------------------------------------------------------------------------
The Retrospect-Framework is licensed under the Creative Commons Attribution-Non-Commercial-No
Derivative Works 3.0 Unported License. To view a copy of this licence, visit 
http://creativecommons.org/licenses/by-nc-nd/3.0/ or send a letter to Creative Commons, 
171 Second Street, Suite 300, San Francisco, California 94105, USA. Files that belong to 
the Retrospect-Framework have a disclaimer stating that they are licensed under the Creative
Commons Attribution-Non-Commercial-No Derivative Works 3.0 Unported License.

All channels, skins and config.py (further called Retrospect Additions) are free software:
you can redistribute it and/or modify it under the terms of the GNU General Public License 
as published by the Free Software Foundation, either version 3 of the License, or (at your 
option) any later version. Retrospect Additions are distributed in the hope that it will be
useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or 
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more 
details. You should have received a copy of the GNU General Public License along with 
Retrospect Additions. If not, see <http://www.gnu.org/licenses/>.
 
--------------------------------------------------------------------------------------------
 1. Introduction
--------------------------------------------------------------------------------------------
An XBox Media Center script which allows playback of streams from www.uitzendinggemist.nl. 
This version has options for streaming multiple past episodes from different TV Shows.
 
Discussion of the script can be done at this thread at the XBMC Forums. Please post any 
problems/suggestions in either of these threads:
 - http://www.xboxmediacenter.com/forum/showthread.php?p=130060) 
 - Most recent XBMC thread at http://gathering.tweakers.net (Dutch only)

Download the latest version at: 
 - http://www.rieter.net/content/ or use the official Retrospect repository (http://www.rieter.net/content/xot/downloads/#XBMC_Repository)

Direct contact can be done using the following e-mailadres: 
 - uitzendinggemist.vx[@t]gmail[d0t]com

--------------------------------------------------------------------------------------------
 2. Changelog
--------------------------------------------------------------------------------------------

See the changelog.txt file.

--------------------------------------------------------------------------------------------
 3. Skinning
--------------------------------------------------------------------------------------------
For future version of Uitzendinggemist.v2 a build that supports WindowXML is required. Such
a version can be found at the *ussual places*. 

For Developers: New skins need to follow these guidelines to function correctly:

* A skinfolder must be placed inside the folder 'skins'
* Uitzendinggemist uses the same folder-name to lookup the skin as the foldername XBMC is 
  using. So the skinfolder for Uitzendinggemist.v2 should have the same name as the folder 
  in which the XBMC-skin is present. E.g. for MC360: the XBMC skin-folder for MC360 is 
  called 'MC360'. So the folder that holds the skin for Uitzendinggemist.v2 should also be 
  called 'MC360' and should be located in the '<scriptfolder of uitzendinggemist>\skins\' 
  folder (which is usually scripts\uitzendinggemist\skins\'.
  If no identically named folder is found. The skin located in the 'Skins\Default' folder 
  is used.
* Inside the skin-folder should at least be a 'Media' and 'PAL' folder. The Media folder 
  holds all the images and the PAL folder the XML for the PAL oriented skins (See XBMC 
  Wiki for more info on skinning-folders).
* The XML files that need to be present are called 'progwindow.xml' and 'channelwindow.xml'. 
* IMPORTANT: Never remove the items which have ID's. These are mandatory for the script. 
  Their appearance can be changed. But they may NEVER be removed. They should keep their ID's. 
* The 'progwindow.xml' holds all the layout for the main window from where the channels
  can be chosen.
* The 'channelwindow.xml' holds all the layout for the episode windows. This is the windows
  from where you can select the episodes.

If you have made a skin, please mail it to me at uitzendinggemist.vx[@t]gmail[d0t]com so 
it can be included in future releases.

--------------------------------------------------------------------------------------------
 4. Known Limitations
--------------------------------------------------------------------------------------------
* Older XBMC builds do not completely support playing of ASF playlist files and streaming 
will fail. Updating to a more recent build of XBMC will solve the problem.
* Not all Kanalenkiezer channels are working. This is a limitation of the www.kanalenkiezer.nl
website. It cannot be fixed. I can override stream-urls. But therefore I need the correct 
URL's for the stream. You can mail them to: uitzendinggemist.vx[@t]gmail[d0t]com with a clear
description of the channel and stream URL.

--------------------------------------------------------------------------------------------
 4.a Some channels are not working? How come?
--------------------------------------------------------------------------------------------
Very often the problem is not the script but the site that is having the problems! So before
you start posting/writing-e-mails/sending-me-logfiles CHECK THE WEBSITES of the channels 
first. Go to www.uitzendinggemist.nl, www.tien.tv, www.rtl.nl, joox.net and/or 
www.pczapper.tv to see if the websites are up and running. If they are not working, neither
will Uitzendinggemist.v2!
If you have verified that the websites are up and running and the script is still not 
working then start posting/writing-e-mails/sending-me-logfiles, but please, always include
the COMPLETE uzg.log logfile so I can see what the problem is.

--------------------------------------------------------------------------------------------
 5. Acknowledgement
--------------------------------------------------------------------------------------------
The first idea for Retrospect/XBMC Online TV/XOT-Uzg came from a script by
by BaKMaN (http://xbox.readrss.com).

I would like to thank Ian Parker from Evanescent Light Photography 
(http://parkerlab.bio.uci.edu/evlight.htm) for allowing me to use one of his pictures as 
the channel background in the Confluece skin.  

--------------------------------------------------------------------------------------------
 6. Donations
--------------------------------------------------------------------------------------------
The following persons have supported Retrospect by donating (the list is
sorted chronologically):

- David Testas
- Stef Olde Scholtenhuis 
- Gerhard ten Hove 
- J.C. Frerichs 
- Kenny Horbach 
- Laurens De Graaff 
- Stehpan van Rooij
- Niels Walta
- Rene Wieldraaijer
- Bastiaan van Perlo
- Anton Vanhoucke
- Niels van den Boogaard
- Ferry Plekkenpol
- Michel Bos 
- M. Spaans 
- Rogier Duurkoop 
- Jonthe Grotenhuis 
- Maurice van Trijffel 
- Bjorn Stam 
- Prism Open Source 
- Serge Kapitein 
- Robbert Hilgeman 
- Jorn Luttikhold 
- Tom de Goeij
- Gecko (Martijn Pet)
- Henri Lier 
- Edwin Endstra 
- Fabian Labohm 
- Jeroen van den Burg 
- Ronald Geerlings 
- Simon Algera 
- Floris Dirkzwager 
- Jurjen van Dijk 
- J. Tebbes 
- Dennis808 
- Joost Wouterse 
- Slashbot28 
- Jasper Westerhof 
- Jacques Overdijk 
- Ramon Broekhuijzen
- Eymert Versteegt
- Rick van Venrooij 
- Frans Hondeman 
- RSJ Kok 
- Jamie Janssen 
- Thomas Novin 
- Emiel Havinga 
- De php programmeur 
- Tijs Gerritsen  
- Bonny Gijzen
- Dennis van Kapel
- Cameq
- Bart Macco
- Markus Sjöström
- Mathijs Groothuis
- Rene Popken
- KEJ Kamperman
- Angelo Potter
- Athlete Hundrafemtionio
- Dennis Brekelmans
- Ted Backman
- Michiel Klooster
- Webframe.NL
- Jan Willemsen
- Marcin Holmstrom
- Örjan Magnusson
- M H Jongen
- Ola Lindberg
- Elcyion
- Dennis van Kapel
- Pieter Geljon
- Andreas Ljunggren
- Miroslav Puskas
- Floris van de Kamer
- Walter Bressers
- Sjoerd Molenaar
- Patrik Johansson
- Willy van Knippenberg
- Stephan van Rooij
- D J vd Wielen 
- Erik Bots
- Alexander Jongeling
- Robert Thörnberg
- Tom Urlings
- Dirk Jeroen Breebaart
- Hans Nijhuis
- Michel ten Hove
- Rick van Venrooij
- Mattias Lindblad
- Anton Opgenoort
- Jasper van den Broek
- Dick Branderhorst
- Mans Jonasson
- Frans Dijkstra
- Michael Forss
- Dick Verwoerd
- Dimitri Olof Areskogh
- Andreas Hägg
- Oscar Gala y Hondema
- Tjerk Pruyssers
- Ramon de Klein
- Wouter Maan
- Thomas Novin
- Arnd Brugman
- David Kvarnberg
- Jasper van den Broek
- Jeroen Koning 
- Saskia Dijk
- Erik Hond
- Frank Hart
- Rogier Werschkull
- Chris Evertz
- Reinoud Vaandrager
- Lucas van der Haven
- Robert Persson
- Harm Verbeek
- Lars lessel
- Just van den Broecke
- Arvid van Kasteel
- G.F.P. van Dijck
- Thijs van Nuland
- Mathijs van der Kooi
- Michael Rydén
- Jelmer Hartman
- Tirza Bosma
- Tijmen Klein
- Chris de Jager
- Albert Kaufman
- Erik Abbevik
- Scott Beijn
- Peter van der Velden
- Jens Lindberg
- Derek Smit
- Wilbert Schoenmakers
- Bastiaan Wanders
- Maarten Zeegers
- Daan Derksen
- Fredrik Ahl
- Johannes G H de Wildt
- Arthur de Werk
- B van den Heuvel
- Rowan van Berlo
- Chris Neddermeijer
- Willem Goudsbloem
- Videotools.net
- Antoinet.com
- Edwin Eefting
- Marco Bakker
- Fredrik Wendland
- Daniel Harkin
- Pieter Cornelis Brinkman
- Tommy Herman
- Mikael Eklund
- Bob Visser
- Wouter Haring
- Sander van der Knijff
- Edwin Stol
- Eric R Dunbar
- michael kwanten
- Ron Kamphuis
- Marielle Bannink
- F W Jansen
- Harold de Wit
- Jim Bevenhall
- Max Faber
- Remon Varkevisser
- Thomas Lundgren
- Arjan Dekker
- Herman Greeven
- Dick Branderhorst
- Joris Overzet
- Hans Voorwinden
- Matthijs Engering
- Andreas Limber
- Igor Jellema
- Henric Ericsson
- Vardan Sarkisian
- Stefan Zwanenburg
- Dirk Jeroen Breebaart
- Paul Versteeg
- Wim Til
- Op Vos
- Jason Muller
- Roland Hansen
- Jeffrey Allen
- Michel van Verk
- Marcel Van Dijk
- Dimitri Huisman
- Peter Werkander
- Mikael Eriksson
- Martin Wikstrand
- Arjan de Jong
- Jan-Åke Skoglund
- Eric Smit
- G.F.P. van Dijck
- Jan Papenhove
- Herman Driessen
- Matias Toftrup
- Bob Langerak
- Martien Wijnands
- Mark Oost
- Chris Evertz
- David Embrechts
- Roeland Koevoets
- John Poussart
- Pieter Geljon
- Josef Gårdstam
- Paul Moes
- Marco Beeren
- Bulent Malgaz
- G Hosmar
- Robert Klep
- Bas van Marwijk
- Thomas Pettersson
- Peter Oosterhoff
- Alexander Kleyn van Willigen
- Onno Ruijsbroek
- Cornelis Pasma
- Roy van Hal
- Henrik Sjöholm
- Christian Ahlin
- Gerben Roest
- Koen Vermeulen
- Christian Koster
- Johan Bryntesson
- Freek Langeveld
- Jasper Koehorst
- Jaco Vos
- Carolina Tovar
- Mats Nordstrom
- Geert Jan Kalfsbeek
- Martin Alvin
- Anders Sandblad
- Bas van Deursen
- S Goudswaard
- Ruben Jan Groot Nibbelink
- Rogier van der Wel
- Arjen de Jong
- Theo Schoen
- Vincent Muis
- Ruth de Groot
- Nils Smits
- Martin Tullberg
- Lucas Weteling
- Nico Olij
- Josef Salberg
- Remco Lam
- Ton Engwirda
- Vincenzo messina
- Stephanus René van Amersfoort
- Rikard Palmer
- Russell Buijsse
- Geert Bax
- Hermandus Jan Marinus Wijnen
- Martijn Boon
- F.M.E.J Huang
- Mikael Eriksson
- Maryse Ellensburg
- Balder Wolf
- Koen Mulder
- Jan Riemens
- Koos Stoffels
- Rob van Houtert
- Samuel Zayas
- Jos Verdoorn
- Patric Sundström
- Henrik Nyberg
- Thetmar Wiegers
- Marco Kerstens
- Richard Willems
- Henk Haan
- Michel van Verk
- Hans Filipsson
- Magnus Bertilsson
- Sean Berger
- LHM Damen
- Theo Jansen
- René Mulder
- Andrei Neculau
- Fred Selders
- Alfred Johansson
- Adri Domeni
- Peter Adriaanse
- Andre Verbücheln
- Frank Kraaijeveld
- Thomas Stefan Nugter
- Robert Mast
- Daniel Skagerö
- Christian Jivenius
- Joost Vande Winkel
- Johan Asplund
- Björn Axelsson
- Gunilla Westermark
- Tobbe Eriksson
- Bram De Waal
- Michiel Ton
- Hans Filipsson
- Micha Van Wijngaarden
- Daniel Sandman
- Johan Johansson
- Andreas Rehnmark
- Jan Den Tandt
- Theo Schoen
- Daniel Skagerö
- Robert Rutherford
- Ulf Svensson
- Bert Olsson
- Svante Dackemyr
- Koen Bekaert
- Rob Hermans
- Marcin Rönndahl
- Robert Smedjeborg
- Bo Johansson
- Olivier De Groote
- Robin Lövgren
- Koen Bekaert (second donation!)
- Mahamed Zishan Khan
- Tom Mertens
- Stian Ringstad
- Per Arne Jonsson
- Niels Van den Put
- Jan Tiels
- Theo Schoen
- Anton Driesprong
- Bart Coninckx
- Rogier Versluis
- Bo Johansson
- Ola Stensson
- Mathijs Groothuis
- Sune Filipsson
- Leif Ohlsson
- Benjamin Jacobs
- Koen De Buck
- Hans Filipsson
- Dejan Dozic
- Roeland Vanraepenbusch
