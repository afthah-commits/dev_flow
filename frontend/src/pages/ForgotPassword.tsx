import React from "react";
import { Link } from "react-router-dom";

export default function ForgotPassword() {
  return (
    <div className="space-y-6">
      <h3 className="text-xl font-medium text-white mb-6">Reset Password</h3>
      <p className="text-gray-400 text-sm mb-4">Password reset is not implemented in Phase 1.</p>
      <Link to="/login" className="block text-center text-sm text-blue-500 hover:text-blue-400">
        Return to sign in
      </Link>
    </div>
  );
}
