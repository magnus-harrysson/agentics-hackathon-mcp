import {PaymentsClient} from "./paymentsClient.js";
import {v4 as uuidv4} from "uuid";

export interface OrderItem {
  productId: string;
  quantity: number;
  price: number;
}

export interface Order {
  paymentId?: string;
  id: string;
  items: OrderItem[];
  totalAmount: number;
  currency: string;
  status: "pending" | "completed" | "cancelled";
  createdAt: Date;
  updatedAt: Date;
}

export class OrderService {
  private orders = new Map<string, Order>();
  private paymentsClient: PaymentsClient;

  constructor(paymentsClient: PaymentsClient) {
    this.paymentsClient = paymentsClient;
  }

  async createOrder(items: OrderItem[], currency: string): Promise<Order> {
    const id = uuidv4();
    const totalAmount = items.reduce((sum, item) => sum + item.quantity * item.price, 0);
    const newOrder: Order = {
      id,
      items,
      totalAmount,
      currency,
      status: "pending",
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    this.orders.set(id, newOrder);

    try {
      const payment = await this.paymentsClient.createPayment({
        amountCents: totalAmount,
        currency: currency,
      });
      newOrder.paymentId = payment.id;
      this.orders.set(id, newOrder);
      this.pollPaymentStatus(id, payment.id);
      console.log(`Payment created for order: ${id}`);
    } catch (error) {
      console.error(`Failed to create payment for order ${id}:`, error);
      newOrder.status = "cancelled";
      this.orders.set(id, newOrder);
      throw new Error("Payment failed, order cancelled.");
    }

    console.log(`Order created: ${id}`);

    return newOrder;
  }

  async getOrder(id: string): Promise<Order | undefined> {
    return this.orders.get(id);
  }

  private pollPaymentStatus(orderId: string, paymentId: string) {
    const interval = setInterval(async () => {
      try {
        const paymentStatus = await this.paymentsClient.getPayment(paymentId);
        if (paymentStatus.status === "completed") {
          await this.updateOrderStatus(orderId, "completed");
          clearInterval(interval);
          console.log(`Order ${orderId} updated to completed as payment ${paymentId} is completed.`);
        } else if (paymentStatus.status === "failed" || paymentStatus.status === "cancelled") {
          await this.updateOrderStatus(orderId, "cancelled");
          clearInterval(interval);
          console.log(`Order ${orderId} cancelled as payment ${paymentId} is ${paymentStatus.status}.`);
        }
      } catch (error) {
        console.error(`Error polling payment status for payment ${paymentId}:`, error);
        clearInterval(interval);
      }
    }, 5000);
  }

  async updateOrderStatus(
    id: string,
    status: "pending" | "completed" | "cancelled",
  ): Promise<Order | undefined> {
    const order = this.orders.get(id);
    if (order) {
      order.status = status;
      order.updatedAt = new Date();
      this.orders.set(id, order);
      console.log(`Order ${id} status updated to ${status}`);
    }
    return order;
  }
}
