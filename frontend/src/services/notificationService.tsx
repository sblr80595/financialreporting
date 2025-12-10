import toast, { Toast, ToastOptions } from 'react-hot-toast';
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react';
import React from 'react';

interface CustomToastProps {
  t: Toast;
  message: string;
  icon: React.ReactNode;
  iconBgColor: string;
  iconColor: string;
}

const CustomToast: React.FC<CustomToastProps> = ({ t, message, icon, iconBgColor, iconColor }) => (
  <div
    className={`${
      t.visible ? 'animate-enter' : 'animate-leave'
    } max-w-md w-full bg-white shadow-lg rounded-lg pointer-events-auto flex ring-1 ring-black ring-opacity-5`}
  >
    <div className="flex-1 w-0 p-4">
      <div className="flex items-start">
        <div className={`flex-shrink-0 ${iconBgColor} rounded-full p-2`}>
          <div className={iconColor}>
            {icon}
          </div>
        </div>
        <div className="ml-3 flex-1">
          <p className="text-sm font-medium text-gray-900">{message}</p>
        </div>
      </div>
    </div>
    <div className="flex border-l border-gray-200">
      <button
        onClick={() => toast.dismiss(t.id)}
        className="w-full border border-transparent rounded-none rounded-r-lg p-4 flex items-center justify-center text-sm font-medium text-gray-600 hover:text-gray-500 focus:outline-none"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  </div>
);

const defaultOptions: ToastOptions = {
  duration: 4000,
  position: 'top-right',
};

export const notificationService = {
  success: (message: string, options?: ToastOptions) => {
    return toast.custom(
      (t) => (
        <CustomToast
          t={t}
          message={message}
          icon={<CheckCircle className="w-5 h-5" />}
          iconBgColor="bg-green-100"
          iconColor="text-green-600"
        />
      ),
      { ...defaultOptions, ...options }
    );
  },

  error: (message: string, options?: ToastOptions) => {
    return toast.custom(
      (t) => (
        <CustomToast
          t={t}
          message={message}
          icon={<XCircle className="w-5 h-5" />}
          iconBgColor="bg-red-100"
          iconColor="text-red-600"
        />
      ),
      { ...defaultOptions, duration: 6000, ...options }
    );
  },

  warning: (message: string, options?: ToastOptions) => {
    return toast.custom(
      (t) => (
        <CustomToast
          t={t}
          message={message}
          icon={<AlertTriangle className="w-5 h-5" />}
          iconBgColor="bg-yellow-100"
          iconColor="text-yellow-600"
        />
      ),
      { ...defaultOptions, duration: 5000, ...options }
    );
  },

  info: (message: string, options?: ToastOptions) => {
    return toast.custom(
      (t) => (
        <CustomToast
          t={t}
          message={message}
          icon={<Info className="w-5 h-5" />}
          iconBgColor="bg-blue-100"
          iconColor="text-blue-600"
        />
      ),
      { ...defaultOptions, ...options }
    );
  },

  promise: <T,>(
    promise: Promise<T>,
    messages: {
      loading: string;
      success: string | ((data: T) => string);
      error: string | ((error: any) => string);
    },
    options?: ToastOptions
  ) => {
    return toast.promise(
      promise,
      {
        loading: messages.loading,
        success: (data) => {
          const msg = typeof messages.success === 'function' ? messages.success(data) : messages.success;
          return msg;
        },
        error: (error) => {
          const msg = typeof messages.error === 'function' ? messages.error(error) : messages.error;
          return msg;
        },
      },
      { ...defaultOptions, ...options }
    );
  },

  loading: (message: string, options?: ToastOptions) => {
    return toast.loading(message, { ...defaultOptions, ...options });
  },

  dismiss: (toastId?: string) => {
    toast.dismiss(toastId);
  },

  dismissAll: () => {
    toast.dismiss();
  },
};

export default notificationService;
