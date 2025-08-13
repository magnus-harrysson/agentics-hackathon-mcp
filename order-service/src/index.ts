import express, {Application} from "express";
import {OrderItem, OrderService} from "./orderService.js";
import {PaymentsClient} from "./paymentsClient.js";

const port = process.env.PORT || 3000;
const app: Application = express();
app.use(express.json());

const service = new OrderService(new PaymentsClient(process.env.PAYMENTS_URL || "http://localhost:4010"));

interface CreateOrderRequestBody {
  items: OrderItem[];
  currency: string;
}

app.post("/order", async (req, res) => {
  try {
    const {items, currency}: CreateOrderRequestBody = req.body;
    if (!items || !Array.isArray(items) || items.length === 0 || !currency) {
      return res.status(400).json({message: "Invalid order data. 'items' and 'currency' are required."});
    }
    const newOrder = await service.createOrder(items, currency);
    return res.status(201).json(newOrder);
  } catch (error: any) {
    return res.status(500).json({message: error.message});
  }
});

app.listen(port, () => {
  console.log(`service listening on port ${port}`);
});
