import {describe, expect, test} from "vitest";
import {OrderService} from "./orderService.js";
import {PaymentsClient} from "./paymentsClient.js";

describe("orderService", () => {
  const paymentsClient = new PaymentsClient("http://localhost:4010");
  const service = new OrderService(paymentsClient);

  test("create order", async () => {
    const order = await service.createOrder(
      [
        {
          productId: "product",
          price: 100,
          quantity: 1,
        },
      ],
      "USD",
    );

    expect(order).toBeDefined();
  });
});
