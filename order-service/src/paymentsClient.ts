export interface CreatePaymentRequest {
  amountCents: number;
  currency: string;
}

export interface Payment {
  id: string;
  status: string;
  amountCents: number;
  currency: string;
}

export class PaymentsClient {
  private readonly baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async createPayment(request: CreatePaymentRequest): Promise<Payment> {
    try {
      const response = await fetch(`${this.baseUrl}/payments`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Failed to create payment: ${response.statusText}`);
      }

      return (await response.json()) as Payment;
    } catch (error) {
      console.error("Error creating payment:", error);
      throw error;
    }
  }

  async getPayment(id: string): Promise<Payment> {
    try {
      const response = await fetch(`${this.baseUrl}/payments/${id}`);

      if (!response.ok) {
        throw new Error(`Failed to get payment: ${response.statusText}`);
      }

      return (await response.json()) as Payment;
    } catch (error) {
      console.error("Error getting payment:", error);
      throw error;
    }
  }
}
