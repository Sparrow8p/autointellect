import { Link } from 'react-router-dom'

export function Brand({ inverse = false }: { inverse?: boolean }) {
  return (
    <Link to="/home" aria-label="Авто-Интеллект — главная" className="brand-link">
      <span aria-hidden="true" className={`brand-mark ${inverse ? 'bg-lime text-forest' : 'bg-forest text-white'}`}>
        А
      </span>
      <span className={`brand-title ${inverse ? 'text-white' : 'text-ink'}`}>
        Авто-Интеллект
      </span>
    </Link>
  )
}
