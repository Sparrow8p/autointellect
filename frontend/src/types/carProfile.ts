export interface CarProfileDraft {
  brand: string
  model: string
  year: string
  mileage: string
  region: string
  saveToProfile: boolean
}

export const emptyCarProfile: CarProfileDraft = {
  brand: '',
  model: '',
  year: '',
  mileage: '',
  region: '',
  saveToProfile: true,
}
