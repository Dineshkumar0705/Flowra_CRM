import React from "react";
import * as AvatarPrimitive from "@radix-ui/react-avatar";
import { cn } from "@/utils/cn";

interface AvatarProps {
  src?: string;
  alt?: string;
  name?: string;
  size?: "sm" | "md" | "lg";
}

const sizeClasses = {
  sm: "h-8 w-8 text-xs",
  md: "h-10 w-10 text-sm",
  lg: "h-12 w-12 text-base",
};

const Avatar: React.FC<AvatarProps> = ({
  src,
  alt,
  name,
  size = "md",
}) => {
  const initials = name
    ?.split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  return (
    <AvatarPrimitive.Root
      className={cn(
        "inline-flex items-center justify-center rounded-full bg-indigo-600 text-white font-semibold",
        sizeClasses[size]
      )}
    >
      {src && <AvatarPrimitive.Image src={src} alt={alt || name} />}
      <AvatarPrimitive.Fallback>{initials || "?"}</AvatarPrimitive.Fallback>
    </AvatarPrimitive.Root>
  );
};

export default Avatar;
