import { AuthFrame } from "@/components/shell/auth-frame";
import { RegisterForm } from "@/features/auth/register-form";
import { ar } from "@/messages/ar";

export default function RegisterPage() {
  return (
    <AuthFrame title={ar.register}>
      <RegisterForm />
    </AuthFrame>
  );
}
