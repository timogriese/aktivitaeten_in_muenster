import type { Activity, AddressSuggestion, ExploreRequest, ExploreResponse } from '~/types/explore'

export const aaseeImage = {
  imageUrl: '/images/aasee.jpg',
  imageAlt: 'Segelboote vor dem grünen Ufer des Aasees in Münster',
  imagePosition: 'center bottom',
  imageCredit: {
    author: 'Dietmar Rabich',
    sourceUrl: 'https://commons.wikimedia.org/wiki/File:Münster,_Aasee_--_2021_--_9791.jpg',
    license: 'CC BY-SA 4.0',
    licenseUrl: 'https://creativecommons.org/licenses/by-sa/4.0/',
  },
}

const addresses: AddressSuggestion[] = [
  { id: 'prinzipalmarkt', label: 'Prinzipalmarkt, 48143 Münster', location: { lat: 51.9625, lng: 7.6285 } },
  { id: 'bahnhof', label: 'Hauptbahnhof, Berliner Platz, 48143 Münster', location: { lat: 51.9567, lng: 7.6356 } },
  { id: 'domplatz', label: 'Domplatz, 48143 Münster', location: { lat: 51.9636, lng: 7.6254 } },
  { id: 'schloss', label: 'Schlossplatz 2, 48149 Münster', location: { lat: 51.9637, lng: 7.6133 } },
  { id: 'aasee', label: 'Aaseeterrassen, Adenauerallee 1, 48149 Münster', location: { lat: 51.9569, lng: 7.6162 } },
  { id: 'hafen', label: 'Hafenplatz 1, 48155 Münster', location: { lat: 51.9509, lng: 7.6423 } },
  { id: 'suedpark', label: 'Südpark, Hammer Straße, 48153 Münster', location: { lat: 51.9467, lng: 7.6282 } },
]

// Already selected and ordered demo response. Never filter it using the request.
// All event dates, opening hours, travel times and timing labels are fictional examples.
const activities: Activity[] = [
  {
    id: 'aasee', title: 'Einmal durchatmen am Aasee', category: 'Natur & draußen', kind: 'place',
    description: 'Wasser im Blick, Wind im Haar. Entdecke die grünen Ufer und lass die Stadt für einen Moment hinter dir.',
    detailedDescription: 'Am Aasee ist Platz für eine kleine Pause vom Alltag. Spaziere am Wasser entlang, such dir einen Platz auf der Wiese oder beobachte die Segelboote. Zwischen Uferwegen, weiten Wiesen und Skulpturen findest du deine eigene kleine Auszeit.',
    location: { lat: 51.9505, lng: 7.6102 }, address: 'Aasee, Annette-Allee, 48149 Münster',
    ...aaseeImage,
  },
  {
    id: 'museum', title: 'Neue Perspektiven entdecken', category: 'Kunst & Kultur', kind: 'place',
    description: 'Von alten Meistern zu neuen Ideen: ein Streifzug durch das LWL-Museum für Kunst und Kultur.',
    detailedDescription: 'Mitten am Domplatz treffen Kunst und Architektur aufeinander. Lass dich durch die Sammlung treiben und bleib dort stehen, wo ein Werk deine Neugier weckt.',
    location: { lat: 51.962, lng: 7.6236 }, address: 'Domplatz 10, 48143 Münster',
    imageUrl: '/images/culture.jpg', imageAlt: 'Außenansicht des LWL-Museums für Kunst und Kultur in Münster',
    imageCredit: {
      author: 'J.-H. Janßen',
      sourceUrl: 'https://commons.wikimedia.org/wiki/File:Muenster_LWL_Museum_fuer_Kunst_und_Kultur_36.jpg',
      license: 'CC BY-SA 4.0', licenseUrl: 'https://creativecommons.org/licenses/by-sa/4.0/',
    },
    openingHoursText: 'Dienstag–Sonntag, 10:00–18:00 Uhr',
    timingLabel: 'Geöffnet bis 18:00 Uhr', travelTimeMinutes: 12,
    websiteUrl: 'https://www.lwl-museum-kunst-kultur.de/',
  },
  {
    id: 'pool', title: 'Abtauchen. Auftanken.', category: 'Sport & Bewegung', kind: 'place',
    description: 'Zieh in Ruhe deine Bahnen im Stadtbad Mitte und bekomme den Kopf wieder frei.',
    detailedDescription: 'Ein Sprung ins Wasser und der Alltag wird leiser. Das Stadtbad Mitte ist ein Ausgangspunkt für eine sportliche Pause mitten in Münster.',
    location: { lat: 51.9685, lng: 7.6294 }, address: 'Badestraße 8, 48147 Münster',
    imageUrl: '/images/swim.jpg', imageAlt: 'Backsteinfassade und Glasfront des Stadtbads Mitte in Münster',
    imageCredit: {
      author: 'michiel1972',
      sourceUrl: 'https://commons.wikimedia.org/wiki/File:Hallenbad_-_panoramio.jpg',
      license: 'CC BY-SA 3.0', licenseUrl: 'https://creativecommons.org/licenses/by-sa/3.0/',
    },
    openingHoursText: '07:00–20:00 Uhr',
    timingLabel: 'Geöffnet bis 20:00 Uhr', travelTimeMinutes: 18,
  },
  {
    id: 'botanical', title: 'Eine kleine Reise ins Grüne', category: 'Natur & draußen', kind: 'place',
    description: 'Zwischen Blättern und Blüten: Entdecke den Botanischen Garten hinter dem Schloss.',
    detailedDescription: 'Verwinkelte Wege, große Bäume und Pflanzen aus unterschiedlichen Regionen machen den Botanischen Garten zu einem besonderen Ort. Nimm dir Zeit zum Schauen und entdecke kleine Details am Wegesrand.',
    location: { lat: 51.9637, lng: 7.6079 }, address: 'Schlossgarten 3, 48149 Münster',
    imageUrl: '/images/garden.jpg', imageAlt: 'Teich mit Bäumen im Botanischen Garten Münster im Winter',
    imageCredit: {
      author: 'br-278',
      sourceUrl: 'https://commons.wikimedia.org/wiki/File:Münster_Schloss_Botanischer_Garten_Teich_01.jpg',
      license: 'CC0', licenseUrl: 'https://creativecommons.org/publicdomain/zero/1.0/',
    },
  },
  {
    id: 'harbour-jazz', title: 'Blaue Stunde, warme Klänge', category: 'Musik & Bühne', kind: 'event',
    description: 'Ein entspannter Jazzabend am Hafen mit dem Trio „Nebenan“.',
    detailedDescription: 'Kontrabass, Klavier und Schlagzeug begleiten den Abend am Wasser.',
    location: { lat: 51.9503, lng: 7.6447 }, address: 'Stadthafen, Hafenweg, 48155 Münster',
    imageUrl: '/images/harbour.jpg', imageAlt: 'Blick über Münsters Stadthafen auf Hafenkran und Flechtheimspeicher',
    imageCredit: {
      author: 'Rainer Halama',
      sourceUrl: 'https://commons.wikimedia.org/wiki/File:Münster-Stadthafen-WUS02262.jpg',
      license: 'CC BY-SA 4.0', licenseUrl: 'https://creativecommons.org/licenses/by-sa/4.0/',
    },
    startsAt: '2026-09-25T19:00:00+02:00', endsAt: '2026-09-25T21:30:00+02:00',
    timingLabel: 'Beginnt um 19:00 Uhr', travelTimeMinutes: 22,
  },
  {
    id: 'reading', title: 'Geschichten unter freiem Himmel', category: 'Kunst & Kultur', kind: 'event',
    description: 'Eine kleine Lesung im Grünen. Fiktive Geschichten, ein lauschiger Ort und neue Gedanken.',
    detailedDescription: 'Bei dieser Lesung treffen kurze Geschichten auf eine ruhige Parkkulisse im Südpark.',
    location: { lat: 51.9467, lng: 7.6304 }, address: 'Südpark, 48153 Münster',
    imageUrl: '/images/suedpark.jpg', imageAlt: 'Grüne Wiese und schattenspendende Bäume im Südpark Münster',
    imageCredit: {
      author: 'Eugler',
      sourceUrl: 'https://commons.wikimedia.org/wiki/File:Südpark_in_Münster.JPG',
      license: 'CC BY-SA 3.0', licenseUrl: 'https://creativecommons.org/licenses/by-sa/3.0/',
    },
    startsAt: '2026-09-25T17:00:00+02:00', endsAt: '2026-09-25T18:00:00+02:00',
    timingLabel: '17:00–18:00 Uhr',
  },
]

// Replace only these two functions with GET /api/geocode and POST /api/explore.
export async function geocode(query: string): Promise<AddressSuggestion[]> {
  const normalized = query.trim().toLocaleLowerCase('de-DE')
  return normalized ? structuredClone(addresses.filter(address => address.label.toLocaleLowerCase('de-DE').includes(normalized))) : []
}

export async function explore(request: ExploreRequest): Promise<ExploreResponse> {
  // Future: return await $fetch<ExploreResponse>('/api/explore', { method: 'POST', body: request })
  void request
  return { activities: structuredClone(activities) }
}
