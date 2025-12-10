import axios, { AxiosError, AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import toast from 'react-hot-toast';

export interface ApiError {
  success: false;
  error_code: string;
  message: string;
  details?: Record<string, any>;
  errors?: Array<{
    field?: string;
    message: string;
    code?: string;
  }>;
  timestamp: string;
  request_id?: string;
}

export interface ApiResponse<T = any> {
  success: true;
  data: T;
  message?: string;
  timestamp: string;
  request_id?: string;
}

class ApiService {
  private client: AxiosInstance;
  private retryCount: number = 3;
  private retryDelay: number = 1000;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
      timeout: 120000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError<ApiError>) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean; _retryCount?: number };

        if (error.response?.status === 401) {
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
          return Promise.reject(error);
        }

        if (this.shouldRetry(error) && originalRequest && !originalRequest._retry) {
          originalRequest._retryCount = originalRequest._retryCount || 0;

          if (originalRequest._retryCount < this.retryCount) {
            originalRequest._retryCount++;
            originalRequest._retry = true;

            await this.delay(this.retryDelay * originalRequest._retryCount);
            return this.client(originalRequest);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  private shouldRetry(error: AxiosError): boolean {
    if (!error.response) {
      return true;
    }

    const status = error.response.status;
    return status === 408 || status === 429 || (status >= 500 && status <= 599);
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private handleError(error: AxiosError<ApiError>): never {
    if (error.response?.data) {
      const apiError = error.response.data;
      
      if (apiError.errors && apiError.errors.length > 0) {
        const errorMessages = apiError.errors.map(e => 
          e.field ? `${e.field}: ${e.message}` : e.message
        ).join(', ');
        toast.error(errorMessages);
      } else {
        toast.error(apiError.message || 'An error occurred');
      }

      throw apiError;
    } else if (error.request) {
      const networkError: ApiError = {
        success: false,
        error_code: 'NETWORK_ERROR',
        message: 'Unable to connect to the server. Please check your internet connection.',
        timestamp: new Date().toISOString()
      };
      toast.error(networkError.message);
      throw networkError;
    } else {
      const unknownError: ApiError = {
        success: false,
        error_code: 'UNKNOWN_ERROR',
        message: error.message || 'An unexpected error occurred',
        timestamp: new Date().toISOString()
      };
      toast.error(unknownError.message);
      throw unknownError;
    }
  }

  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    try {
      const response: AxiosResponse<ApiResponse<T>> = await this.client.get(url, config);
      return response.data.data;
    } catch (error) {
      return this.handleError(error as AxiosError<ApiError>);
    }
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    try {
      const response: AxiosResponse<ApiResponse<T>> = await this.client.post(url, data, config);
      return response.data.data;
    } catch (error) {
      return this.handleError(error as AxiosError<ApiError>);
    }
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    try {
      const response: AxiosResponse<ApiResponse<T>> = await this.client.put(url, data, config);
      return response.data.data;
    } catch (error) {
      return this.handleError(error as AxiosError<ApiError>);
    }
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    try {
      const response: AxiosResponse<ApiResponse<T>> = await this.client.delete(url, config);
      return response.data.data;
    } catch (error) {
      return this.handleError(error as AxiosError<ApiError>);
    }
  }

  async uploadFile<T = any>(
    url: string,
    file: File,
    additionalData?: Record<string, any>,
    onUploadProgress?: (progressEvent: any) => void
  ): Promise<T> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      if (additionalData) {
        Object.entries(additionalData).forEach(([key, value]) => {
          formData.append(key, value);
        });
      }

      const response: AxiosResponse<ApiResponse<T>> = await this.client.post(url, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress,
      });

      return response.data.data;
    } catch (error) {
      return this.handleError(error as AxiosError<ApiError>);
    }
  }

  async downloadFile(url: string, filename: string): Promise<void> {
    try {
      const response = await this.client.get(url, {
        responseType: 'blob',
      });

      const blob = new Blob([response.data]);
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      return this.handleError(error as AxiosError<ApiError>);
    }
  }

  getClient(): AxiosInstance {
    return this.client;
  }
}

export const apiService = new ApiService();
export default apiService;
