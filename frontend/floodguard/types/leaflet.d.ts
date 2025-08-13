declare module 'leaflet' {
  export * from 'leaflet'
}

// Extend the Leaflet types if needed
declare global {
  namespace L {
    interface Icon {
      Default: {
        prototype: any
        mergeOptions(options: any): void
      }
    }
  }
}
