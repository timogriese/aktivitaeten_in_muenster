import type { AddressSuggestion, ExploreRequest, ExploreResponse } from '~/types/explore'

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

// Fixed demo list - no geocoding backend yet.
const addresses: AddressSuggestion[] = [
  { id: 'prinzipalmarkt', label: 'Prinzipalmarkt, 48143 Münster', location: { lat: 51.9625, lng: 7.6285 } },
  { id: 'bahnhof', label: 'Hauptbahnhof, Berliner Platz, 48143 Münster', location: { lat: 51.9567, lng: 7.6356 } },
  { id: 'domplatz', label: 'Domplatz, 48143 Münster', location: { lat: 51.9636, lng: 7.6254 } },
  { id: 'schloss', label: 'Schlossplatz 2, 48149 Münster', location: { lat: 51.9637, lng: 7.6133 } },
  { id: 'aasee', label: 'Aaseeterrassen, Adenauerallee 1, 48149 Münster', location: { lat: 51.9569, lng: 7.6162 } },
  { id: 'hafen', label: 'Hafenplatz 1, 48155 Münster', location: { lat: 51.9509, lng: 7.6423 } },
  { id: 'suedpark', label: 'Südpark, Hammer Straße, 48153 Münster', location: { lat: 51.9467, lng: 7.6282 } },
]

export async function geocode(query: string): Promise<AddressSuggestion[]> {
  const normalized = query.trim().toLocaleLowerCase('de-DE')
  return normalized ? structuredClone(addresses.filter(address => address.label.toLocaleLowerCase('de-DE').includes(normalized))) : []
}

// Proxied to the Spring Boot backend, see routeRules in nuxt.config.ts.
export async function explore(request: ExploreRequest): Promise<ExploreResponse> {
  return await $fetch<ExploreResponse>('/api/explore', { method: 'POST', body: request })
}
