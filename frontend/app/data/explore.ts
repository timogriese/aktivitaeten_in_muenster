import type { ExploreRequest, ExploreResponse } from '~/types/explore'

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

// Proxied to the Spring Boot backend, see routeRules in nuxt.config.ts.
export async function explore(request: ExploreRequest): Promise<ExploreResponse> {
  return await $fetch<ExploreResponse>('/api/explore', { method: 'POST', body: request })
}
