export interface Coordinates {
  lat: number
  lng: number
}

export interface AddressSuggestion {
  id: string
  label: string
  location: Coordinates
}

export interface ExploreRequest {
  origin: Coordinates
  startsAt: string
  availableMinutes: number
}

export interface Activity {
  id: string
  title: string
  description: string
  detailedDescription?: string
  kind: 'place' | 'event'
  category: string
  location: Coordinates
  address: string
  imageUrl?: string
  websiteUrl?: string
  startsAt?: string
  endsAt?: string
  openingHoursText?: string
  travelTimeMinutes?: number
  timingLabel?: string
}

export interface ExploreResponse {
  activities: Activity[]
}
