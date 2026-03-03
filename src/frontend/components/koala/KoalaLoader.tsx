export default function KoalaLoader() {
  return (
    <div className="flex flex-col items-center justify-center gap-3">
      <div className="relative w-16 h-16 animate-spin-slow">
        <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
          <ellipse cx="32" cy="38" rx="18" ry="20" fill="#8B6347" />
          <circle cx="16" cy="22" r="10" fill="#8B6347" />
          <circle cx="48" cy="22" r="10" fill="#8B6347" />
          <circle cx="32" cy="34" r="14" fill="#C4956A" />
          <ellipse cx="32" cy="40" rx="8" ry="5" fill="#8B6347" />
          <circle cx="27" cy="30" r="3" fill="#3D2B1F" />
          <circle cx="37" cy="30" r="3" fill="#3D2B1F" />
          <ellipse cx="32" cy="36" rx="4" ry="3" fill="#5C3D2E" />
          <rect x="28" y="52" width="8" height="12" rx="4" fill="#5C8A3C" />
          <ellipse cx="32" cy="52" rx="12" ry="4" fill="#5C8A3C" />
        </svg>
      </div>
      <p className="text-koala-brown text-sm font-medium animate-pulse">考拉正在思考…</p>
    </div>
  )
}
