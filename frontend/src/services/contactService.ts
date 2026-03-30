import apiClient from "./apiClient";
import { ApiResponse, Contact } from "@/types";

interface GetContactsParams {
  page?: number;
  page_size?: number;
  search?: string;
  tag?: string;
  source?: string;
}

interface CreateContactData {
  first_name: string;
  last_name?: string;
  email?: string;
  phone?: string;
  whatsapp_number?: string;
  company_name?: string;
  job_title?: string;
  source?: string;
  tags?: string[];
}

export const contactService = {
  async getContacts(
    params: GetContactsParams = {}
  ): Promise<ApiResponse<Contact[]>> {
    const response = await apiClient.get("/contacts", { params });
    return response.data;
  },

  async createContact(data: CreateContactData): Promise<ApiResponse<Contact>> {
    const response = await apiClient.post("/contacts", data);
    return response.data;
  },

  async getContact(id: string): Promise<ApiResponse<Contact>> {
    const response = await apiClient.get(`/contacts/${id}`);
    return response.data;
  },

  async updateContact(
    id: string,
    data: Partial<CreateContactData>
  ): Promise<ApiResponse<Contact>> {
    const response = await apiClient.patch(`/contacts/${id}`, data);
    return response.data;
  },

  async deleteContact(id: string): Promise<ApiResponse<any>> {
    const response = await apiClient.delete(`/contacts/${id}`);
    return response.data;
  },

  async rescoreContact(id: string): Promise<ApiResponse<Contact>> {
    const response = await apiClient.post(`/contacts/${id}/rescore`);
    return response.data;
  },
};
