import { AuthFrame } from "@/components/shell/auth-frame";
import { LoginForm } from "@/features/auth/login-form";
import { ar } from "@/messages/ar";

export default function LoginPage() {
  return (
    <AuthFrame title={ar.login}>
      <LoginForm />
    </AuthFrame>
  );
}
