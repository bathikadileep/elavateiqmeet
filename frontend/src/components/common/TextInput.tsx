import React from "react";

interface TextInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  fullWidth?: boolean;
}

export const TextInput = React.forwardRef<HTMLInputElement, TextInputProps>(
  ({ label, error, fullWidth = false, className = "", id, ...props }, ref) => {
    const widthStyle = fullWidth ? "w-full" : "";
    return (
      <div className={`flex flex-col gap-1.5 ${widthStyle}`}>
        {label ? (
          <label htmlFor={id} className="text-sm font-medium text-gray-300 ml-1">
            {label}
          </label>
        ) : null}
        <input
          id={id}
          ref={ref}
          className={`glass-input px-4 py-3 rounded-xl text-base ${widthStyle} ${
            error ? "border-red-500/50 focus:border-red-500" : ""
          } ${className}`}
          {...props}
        />
        {error ? (
          <span className="text-xs text-red-400 font-medium ml-1 mt-0.5">
            {error}
          </span>
        ) : null}
      </div>
    );
  }
);

TextInput.displayName = "TextInput";
export default TextInput;
