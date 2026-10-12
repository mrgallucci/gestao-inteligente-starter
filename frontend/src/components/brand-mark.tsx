import Image from "next/image";

/**
 * Símbolo SARGTECH v0.1 — SVG oficial do pacote de identidade (`public/brand`).
 * `light` = símbolo Cobalt (fundos claros); `dark` = símbolo branco (fundo Midnight).
 */
export default function BrandMark({
  size = 32,
  tone = "light",
  className,
}: {
  size?: number;
  tone?: "light" | "dark";
  className?: string;
}) {
  return (
    <Image
      src={tone === "dark" ? "/brand/sargtech-symbol-white.svg" : "/brand/sargtech-symbol-cobalt.svg"}
      alt="SARGTECH"
      width={size}
      height={size}
      className={className}
      unoptimized
      priority
    />
  );
}
