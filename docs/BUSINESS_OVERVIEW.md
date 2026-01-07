# UNIOSS3 Business Overview

## What is UNIOSS3?

UNIOSS3 is a comprehensive e-commerce platform designed specifically for managing **Furusato Nozei** (hometown tax donation) systems in Japan. The platform enables municipalities to accept tax-deductible donations from citizens and provide them with local products or services in return.

The system supports two main types of stores:
- **Tax Donation Sites** (納税サイト): Municipalities accepting hometown tax donations
- **Regular E-commerce Shops** (一般ストア): Standard online stores for product sales

---

## Core Business Purpose

The primary goal of UNIOSS3 is to facilitate the complete lifecycle of hometown tax donations:

1. **Accept Donations**: Citizens make tax-deductible donations to municipalities
2. **Manage Products**: Municipalities offer local products as "thank-you gifts" for donations
3. **Process Orders**: Handle donation orders from both online stores and physical vending machines
4. **Track Financials**: Manage deals, invoices, and payments between various parties (municipalities, producers, agencies, etc.)
5. **Reward Users**: Operate a coin-based loyalty system where users earn and spend coins

---

## Main Entities and Their Roles

### Stores (Municipalities)
- **What**: Each municipality operates a "store" on the platform
- **Types**: Tax donation site (納税サイト) or regular shop (一般ストア)
- **Purpose**: Accept donations, display products, manage orders
- **Example**: "Kyoto City Store" accepts donations and offers local sake as thank-you gifts

### Orders
- **What**: Donation requests or product purchases made by users
- **Types**: 
  - Tax donation orders (納税注文): Tax-deductible donations
  - Shop orders (物販注文): Regular product purchases
- **Lifecycle**: New → Paid → Shipped → Delivered
- **Example**: User donates ¥10,000 to Kyoto City and receives a bottle of sake

### Products
- **What**: Items offered as thank-you gifts for donations or sold in shops
- **Managed by**: Producers (生産者)
- **Features**: Categories, specifications, inventory, pricing
- **Example**: "Kyoto Premium Sake 720ml" - a product offered by a producer

### Vending Machines (自販機)
- **What**: Physical machines that sell products and create orders automatically
- **Purpose**: Enable in-person product sales at physical locations
- **Integration**: Machines communicate with the system via API to create orders
- **Example**: A vending machine at a train station selling local products

### Coins
- **What**: Loyalty points system with two types:
  - **Common Coins**: Usable across all coin shops in a store
  - **Unique Coins**: Specific to certain coin shop groups
- **Earning**: Users receive coins when making purchases or donations
- **Spending**: Coins can be used to purchase products from coin shops
- **Expiration**: Coins have expiration dates based on store settings
- **Example**: User earns 100 coins from a donation, can spend them later on products

### Deals (取引)
- **What**: Financial agreements that define how money flows between groups
- **Parties**: 
  - **Receiving Group**: The group that receives payment (e.g., producer)
  - **Paying Group**: The group that pays (e.g., municipality)
- **Types**: 
  - Monthly sale percentage
  - Fixed monthly amount
  - Wholesale pricing
  - Per-order fixed amount
  - Coin conversion
  - And more...
- **Purpose**: Automatically calculate how much each party should receive/pay based on sales
- **Example**: A deal where a producer receives 70% of sales from their products sold in a municipality's store

### Invoices
- **What**: Bills generated based on deals and actual order data
- **Purpose**: Calculate and record financial transactions between groups
- **Generation**: Created monthly or per-order based on deal types
- **Example**: Monthly invoice showing a producer should receive ¥500,000 based on their deal with a municipality

### Groups (組織)
- **What**: Organizations that participate in the system
- **Types**: 
  - Municipalities (市町村)
  - Producers (生産者)
  - Agencies (仲介者)
  - Affiliaters (アフィリエイター)
  - Brokers (仲介業者)
- **Purpose**: Represent the various parties involved in the donation ecosystem

### Admins (管理者)
- **What**: System administrators with different roles and permissions
- **Roles**: 
  - Store/Site administrators
  - Tax administrators
  - Producers
  - Shippers
  - Affiliaters
  - Sales staff
- **Purpose**: Manage stores, products, orders, and system configuration

### Users (利用者)
- **What**: End customers who make donations and purchases
- **Features**: Account management, order history, coin balance, address management
- **Example**: A citizen who donates to multiple municipalities throughout the year

---

## How Entities Interact

### Typical Donation Flow

1. **User browses** a municipality's store (tax donation site)
2. **User selects** products they want as thank-you gifts
3. **User places order** (donation request) with payment
4. **Order is created** in the system with status "New"
5. **Payment is processed** (via GMO, Paygent, or other payment gateways)
6. **Order status changes** to "Paid" after payment confirmation
7. **Producer ships** the products
8. **Order status changes** to "Shipped"
9. **User receives** products
10. **Deals are calculated** based on the order
11. **Invoices are generated** for the relevant groups

### Vending Machine Flow

1. **Customer uses** a physical vending machine
2. **Machine sends** order data to the system via API
3. **System creates** order automatically (may create user account if needed)
4. **Order follows** same lifecycle as online orders
5. **Deals and invoices** are calculated the same way

### Coin System Flow

1. **User makes** a purchase or donation
2. **User earns** coins based on store settings
3. **Coins are stored** in user's account (common or unique coins)
4. **User browses** coin shops
5. **User spends** coins to purchase products
6. **Coins expire** after a set period (if configured)

### Deal and Invoice Flow

1. **Admin creates** a deal between two groups (e.g., producer and municipality)
2. **Deal defines** payment terms (percentage, fixed amount, etc.)
3. **Orders are placed** and completed
4. **System calculates** deal amounts based on order data
5. **Invoices are generated** monthly or per-order
6. **Groups receive/pay** according to invoice amounts

---

## Restrictions and Limitations

### ECSite Feature Limitations

Compared to major e-commerce platforms (Amazon, Rakuten, Yahoo Shopping, etc.), the ECSite (frontend) has the following limitations:

#### Product Discovery & Browsing
- **No product search functionality**: Users cannot search for products by keyword, category, or other criteria on the ECSite. Products are only accessible through browsing the top page, product detail pages, and category/genre navigation.
- **No product list/filtering page**: Unlike typical e-commerce sites, there is no dedicated product listing page with filtering options (price range, producer, genre, availability, etc.) available to end users on the frontend.
- **No product sorting options for users**: While the admin panel supports sorting (price low to high, price high to low, newest, etc.), end users cannot sort products on the ECSite frontend.
- **No recently viewed products**: The system does not track or display products that users have recently viewed, which is a common feature on e-commerce sites.
- **No product comparison feature**: Users cannot compare multiple products side-by-side to evaluate specifications, prices, and features.

#### User Engagement & Social Features
- **No customer reviews/ratings display**: Although a `reviews` table exists in the database, customer reviews and ratings are not displayed or collected on the ECSite frontend. This is a standard feature on platforms like Amazon and Rakuten.
- **No wishlist/favorites functionality**: While a `favorites` table exists in the database, users cannot save products to a wishlist or favorites list on the ECSite frontend for later purchase.
- **No social sharing**: Products cannot be shared on social media platforms (Facebook, Twitter, LINE, etc.) directly from the ECSite.
- **No product Q&A section**: Users cannot ask questions about products or see answers from other customers or sellers, which is common on major e-commerce platforms.

#### Product Information & Media
- **No product videos**: Products can only display images; video content (product demonstrations, usage instructions, etc.) is not supported.
- **Limited product image gallery**: While image zoom functionality exists (using Fancybox), the product image gallery experience may be limited compared to modern e-commerce standards.

#### Personalization & Recommendations
- **Limited product recommendations**: While a `product_recommendations` table exists, the system does not provide personalized product recommendations based on user purchase history, browsing behavior, or collaborative filtering algorithms commonly used by major e-commerce sites.
- **No "customers who bought this also bought" feature**: Related products are shown for coin shop products, but there is no algorithm-based recommendation system for regular products based on purchase patterns.

#### Inventory & Availability
- **No stock notification alerts**: Users cannot sign up to receive email notifications when out-of-stock products become available again, a feature commonly found on e-commerce sites.
- **No pre-order functionality**: The system does not support pre-orders for products that are not yet available for purchase.

#### User Experience
- **No multi-language support on frontend**: While the system has language folders (English/Japanese), the ECSite frontend does not appear to support language switching for international users.
- **Limited accessibility features**: The system may not fully comply with modern web accessibility standards (WCAG) that are expected on major e-commerce platforms.

### Order Status Restrictions

- Orders follow strict status transitions: New → Paid → Shipped → Delivered
- Status changes must follow valid transitions (defined in `shipment_status_maps`)
- Cannot skip statuses (e.g., cannot go from New directly to Shipped)

### Store Type Restrictions

- **Tax Donation Sites**: Primarily for accepting tax-deductible donations
- **Regular Shops**: For standard e-commerce sales
- Store type affects order processing, tax calculations, and available features

### Deal Type Restrictions

- Each deal type has specific calculation rules
- Deals have start and end dates
- Deals can be tied to specific vending machines (for monthly sales deals)
- Deal value ranges may apply (tiered pricing based on sales volume)

### Payment Method Limitations

- Payment methods are predefined (credit card, bank transfer, etc.)
- Payment processing is handled by external gateways (GMO, Paygent)
- Some payment methods may not be available for all store types

### Product and Inventory

- Products must belong to a producer
- Inventory is tracked per product specification
- Out-of-stock products cannot be ordered
- Products can be assigned to specific vending machines

### User Account Restrictions

- **Login attempts**: Accounts are locked after 3 failed login attempts
- **Lock duration**: 300 seconds (5 minutes)
- **Password requirements**: Must contain uppercase, lowercase, numbers, and be 8-32 characters
- **Email verification**: Required for account creation

### Administrative Access

- Admins have role-based permissions
- Not all admins can access all features
- Permission checks are enforced throughout the system
- Admin roles include: Store Admin, Tax Admin, Producer, Shipper, Affiliater, Sales

### Data Integrity Rules

- **Soft deletes**: Most entities use `delete_flg` instead of hard deletes
- **Foreign keys**: Database relationships are enforced
- **Transactions**: Critical operations use database transactions
- **Audit trails**: Status changes and important actions are logged

### API Limitations

- Vending machine API requires authentication (checksum validation)
- API endpoints have rate limiting considerations
- JSON data must be properly formatted
- API responses follow a standard format

### Business Rule Constraints

- **Donation amounts**: Must meet minimum requirements for tax deduction
- **Product availability**: Products may have regional restrictions
- **Delivery**: Some products may have delivery restrictions (temperature, region blocks)
- **Tax calculations**: Complex tax rules apply based on product types and deal configurations

---

## Key Business Rules

### Financial Calculations

1. **Deal calculations** are based on actual order data
2. **Invoice generation** happens monthly or per-order based on deal type
3. **Payment distribution** follows deal agreements between groups
4. **Tax handling** varies by product type and deal configuration

### Order Processing

1. Orders cannot be modified after payment
2. Order status changes must be valid transitions
3. Shipment dates are recorded when status changes to "Shipped"
4. Payment dates are recorded when status changes to "Paid"

### Coin Management

1. Coins are earned at purchase/donation time
2. Coins expire based on store configuration
3. Coin usage must not exceed available balance
4. Coin rates may vary by coin shop group

### Product Management

1. Products must have valid producer associations
2. Inventory must be sufficient for orders
3. Products can be assigned to categories
4. Products can be linked to specific vending machines

---

## Common Scenarios

### Scenario 1: User Makes a Donation

1. User visits Kyoto City's tax donation site
2. User selects "Premium Sake Set" (¥10,000)
3. User completes payment via credit card
4. Order is created with status "New"
5. Payment is confirmed, status changes to "Paid"
6. Producer ships the sake, status changes to "Shipped"
7. User receives the product
8. System calculates deal: Producer receives 70% (¥7,000), Municipality keeps 30% (¥3,000)
9. Invoice is generated for the producer

### Scenario 2: Vending Machine Sale

1. Customer approaches a vending machine at a train station
2. Customer selects a product and pays
3. Machine sends order data to UNIOSS3 API
4. System creates order and user account (if needed)
5. Order follows normal processing flow
6. Deal calculations and invoices are generated

### Scenario 3: Coin Usage

1. User has 500 common coins from previous donations
2. User browses coin shops in the store
3. User finds a product costing 300 coins
4. User purchases the product using coins
5. User's coin balance decreases to 200 coins
6. Product is shipped normally

---

## Summary

UNIOSS3 is a complex platform managing the entire ecosystem of hometown tax donations in Japan. It handles everything from user donations and product management to financial settlements between various parties. The system supports both online and physical (vending machine) sales, includes a loyalty coin system, and manages complex deal and invoice calculations.

When working with the system, always consider:
- The current refactoring state (admin_id migration)
- Business rules around orders, deals, and invoices
- User experience flows (donation → product → coins)
- Administrative permissions and role restrictions
- Data integrity and transaction safety

