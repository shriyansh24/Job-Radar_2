import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { changePasswordApi } from "../../api/auth";
import { toast } from "../ui/toastService";
import type { PasswordForm } from "./SettingsTabPanels";

function useSettingsSecurity() {
  const [passwordForm, setPasswordForm] = useState<PasswordForm>({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });

  const changePasswordMutation = useMutation({
    mutationFn: () => changePasswordApi(passwordForm.currentPassword, passwordForm.newPassword),
    onSuccess: () => {
      toast("success", "Password updated");
      setPasswordForm({ currentPassword: "", newPassword: "", confirmPassword: "" });
    },
    onError: () => toast("error", "Password update failed"),
  });

  function submitPasswordChange() {
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      toast("error", "Passwords do not match");
      return;
    }
    changePasswordMutation.mutate();
  }

  return {
    passwordForm,
    passwordPending: changePasswordMutation.isPending,
    setCurrentPassword: (value: string) =>
      setPasswordForm((current) => ({ ...current, currentPassword: value })),
    setNewPassword: (value: string) =>
      setPasswordForm((current) => ({ ...current, newPassword: value })),
    setConfirmPassword: (value: string) =>
      setPasswordForm((current) => ({ ...current, confirmPassword: value })),
    submitPasswordChange,
  };
}

export { useSettingsSecurity };
