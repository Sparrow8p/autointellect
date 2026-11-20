
export const carModels: Readonly<Record<string, readonly string[]>> = {
  LADA: ['Granta', 'Vesta', 'Niva', 'Largus', 'Kalina', 'Priora'],
}

export const carBrands: readonly string[] = Object.keys(carModels)

export const carRegions: readonly string[] = [
  'Свердловская область',
]
